import celery
from celery import current_task
from celery.utils.log import get_task_logger
from flask.ext.login import current_user
import traceback
from wikimetrics.configurables import app, db, queue
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import label, between, and_, or_
from sqlalchemy.exc import OperationalError
from wikimetrics.utils import deduplicate_by_key
from wikimetrics.models import (
    MediawikiUser, CohortStore, CohortUserStore, WikiUserStore, CohortWikiUserStore,
)
from wikimetrics.enums import CohortUserRole


task_logger = get_task_logger(__name__)


@queue.task()
def async_validate(validate_cohort):
    task_logger.info('Running Cohort Validation job')
    validate_cohort.run()
    return 'DONE'


class ValidateCohort(object):
    """
    An instance of this class is responsible for:
    * Creating a cohort, or loading an existing one
    * Re-validating the cohort's existing users or validating a CSV record list
    * Validating asynchronously and updating the database as it goes
    * Updating the cohort to validated == True once all users have been validated
    """
    task = async_validate

    def __init__(self, cohort):
        """
        Parameters:
            cohort  : an existing cohort
            config  : global config, we need to know
                if we are on dev or testing to validate project name

        Instantiates with these properties:
            cohort_id               : id of an existing cohort with validated == False
            validate_as_user_ids    : if True, records will be checked against user_id
                                      if False, records are checked against user_name
        """
        self.cohort_id = cohort.id
        self.validate_as_user_ids = cohort.validate_as_user_ids

    @classmethod
    def from_upload(cls, cohort_upload, owner_user_id, session=None):
        """
        Create a new cohort and validate a list of uploaded users for it

        Parameters:
            cohort_upload   : the cohort upload form, parsed by WTForms
            owner_user_id   : the Wikimetrics user id that is uploading

        Returns:
            An instance of ValidateCohort
        """
        cohort = CohortStore(
            name=cohort_upload.name.data,
            description=cohort_upload.description.data,
            default_project=cohort_upload.project.data,
            enabled=True,
            public=False,
            validated=False,
            validate_as_user_ids=cohort_upload.validate_as_user_ids.data == 'True',
        )
        centralauth = getattr(cohort_upload, 'centralauth', None)
        if centralauth is not None and centralauth.data is True:
            cohort.class_name = 'CentralAuthCohort'
        session = session or db.get_session()
        try:
            session.add(cohort)
            session.commit()

            cohort_user = CohortUserStore(
                user_id=owner_user_id,
                cohort_id=cohort.id,
                role=CohortUserRole.OWNER
            )
            session.add(cohort_user)
            session.commit()

            session.execute(
                WikiUserStore.__table__.insert(), [
                    {
                        'raw_id_or_name'    : record['raw_id_or_name'],
                        'project'           : record['project'],
                        'valid'             : None,
                        'reason_invalid'    : '',
                        'validating_cohort' : cohort.id,
                    } for record in cohort_upload.records
                ]
            )
            session.commit()
            return cls(cohort)
        except Exception, e:
            session.rollback()
            app.logger.error(str(e))
            return None

    def run(self):
        session = db.get_session()
        cohort = session.query(CohortStore).get(self.cohort_id)
        cohort.validation_queue_key = current_task.request.id
        session.commit()
        self.validate_records(session, cohort)

    def validate_records(self, session, cohort):
        """
        Fetches the wiki_user(s) already added for self.cohort_id and validates
        their raw_id_or_name field against their stated project as either a user_id
        or user_name.  Once done, sets the valid state and deletes any duplicates.
        Then, it finishes filling in the data model by inserting corresponding
        records into the cohort_wiki_users table.

        This is meant to execute asynchronously on celery

        Parameters
            session : an active wikimetrics db session to use
            cohort  : the cohort to validate; must belong to session
        """
        # reset the cohort validation status so it can't be used for reports
        cohort.validated = False
        session.execute(
            WikiUserStore.__table__.update().values(valid=None).where(
                WikiUserStore.validating_cohort == cohort.id
            )
        )
        session.execute(CohortWikiUserStore.__table__.delete().where(
            CohortWikiUserStore.cohort_id == cohort.id
        ))
        session.commit()

        wikiusers = session.query(WikiUserStore) \
            .filter(WikiUserStore.validating_cohort == cohort.id) \
            .all()

        deduplicated = deduplicate_by_key(
            wikiusers,
            lambda r: (
                r.raw_id_or_name,
                normalize_project(r.project) or r.project
            )
        )

        wikiusers_by_project = {}
        for wu in deduplicated:
            normalized_project = normalize_project(wu.project)
            if normalized_project is None:
                wu.reason_invalid = 'invalid project: {0}'.format(wu.project)
                wu.valid = False
                continue

            wu.project = normalized_project
            if wu.project not in wikiusers_by_project:
                wikiusers_by_project[wu.project] = []
            wikiusers_by_project[wu.project].append(wu)

            # validate bunches of records to update the UI but not kill performance
            if len(wikiusers_by_project[wu.project]) > 999:
                validate_users(
                    wikiusers_by_project[wu.project],
                    wu.project,
                    self.validate_as_user_ids
                )
                session.commit()
                wikiusers_by_project[wu.project] = []

        # validate anything that wasn't big enough for a batch
        for project, wikiusers in wikiusers_by_project.iteritems():
            if len(wikiusers) > 0:
                validate_users(wikiusers, project, self.validate_as_user_ids)
        session.commit()

        session.execute(
            CohortWikiUserStore.__table__.insert(), [
                {
                    'cohort_id'     : cohort.id,
                    'wiki_user_id'  : wu.id,
                } for wu in deduplicated
            ]
        )

        # clean up any duplicate wiki_user records
        session.execute(WikiUserStore.__table__.delete().where(and_(
            WikiUserStore.validating_cohort == cohort.id,
            WikiUserStore.id.notin_([wu.id for wu in deduplicated])
        )))
        cohort.validated = True
        session.commit()

    def __repr__(self):
        return '<ValidateCohort("{0}")>'.format(self.cohort_id)


def normalize_project(project):
    """
    Decides whether the name of the project is a valid one
    There are differences in db names in local setup versus vagrant setup
    While local setup uses enwiki mediawiki vagrant uses wiki
    We let 'wiki' be an acceptable name in development by injecting it into
    the project_host_map returned by the database singleton, db
    """
    project = project.strip().lower()
    if project in db.get_project_host_map():
        return project
    else:
        # try adding wiki to end
        new_proj = project + 'wiki'
        if new_proj not in db.get_project_host_map():
            return None
        else:
            return new_proj


def validate_users(wikiusers, project, validate_as_user_ids):
    """
    Parameters
        wikiusers               : the wikiusers with a candidate mediawiki_username
        project                 : the project these wikiusers should belong to
        validate_as_user_ids    : if True, records will be checked against user_id
                                  if False, records are checked against user_name
    """
    users_dict = {wu.raw_id_or_name : wu for wu in wikiusers}
    valid_project = True

    # validate
    try:
        session = db.get_mw_session(project)
        if validate_as_user_ids:
            keys_as_ints = [int(k) for k in users_dict.keys() if k.isdigit()]
            clause = MediawikiUser.user_id.in_(keys_as_ints)
        else:
            clause = MediawikiUser.user_name.in_(users_dict.keys())
        matches = session.query(MediawikiUser).filter(clause).all()

    # no need to roll back session because it's just a query
    except OperationalError:
        # caused by accessing an unknown database
        # as it can be recovered, no need to reraise the error
        # but all users have to be marked as invalid
        msg = traceback.format_exc()
        task_logger.warning(msg)
        matches = []
        valid_project = False

    except Exception, e:
        msg = traceback.format_exc()
        task_logger.error(msg)
        raise e

    # update results
    for match in matches:
        if validate_as_user_ids:
            key = str(match.user_id)
        else:
            key = match.user_name

        users_dict[key].mediawiki_username = match.user_name
        users_dict[key].mediawiki_userid = match.user_id
        users_dict[key].valid = True
        users_dict[key].reason_invalid = None
        # remove valid matches
        users_dict.pop(key)

    # mark the rest invalid
    # key is going to be a string if bindings are correct, but careful!
    # it might be a string with chars that cannot be represented w/ ascii
    # the 'reason_invalid' does not need to have the user_id,
    # it is on the record on the table
    for key in users_dict.keys():
        if not valid_project:
            reason_invalid = 'invalid project'
        elif validate_as_user_ids:
            reason_invalid = 'invalid user_id'
        else:
            reason_invalid = 'invalid user_name'
        users_dict[key].reason_invalid = reason_invalid
        users_dict[key].valid = False
