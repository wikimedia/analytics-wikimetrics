import celery
from celery import current_task
from celery.utils.log import get_task_logger
from flask.ext.login import current_user
from wikimetrics.configurables import app, db, queue
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import label, between, and_, or_
from wikimetrics.utils import deduplicate_by_key
from wikimetrics.models import (
    MediawikiUser, Cohort, CohortUser, CohortUserRole, WikiUser, CohortWikiUser
)


task_logger = get_task_logger(__name__)


@queue.task()
def async_validate(validate_cohort):
    task_logger.info('Running Cohort Validation job')
    validate_cohort.run()
    return validate_cohort


class ValidateCohort(object):
    """
    An instance of this class is responsible for:
    * Creating a cohort, or loading an existing one
    * Re-validating the cohort's existing users or validating a CSV record list
    * Validating asynchronously and updating the database as it goes
    * Updating the cohort to validated == True once all users have been validated
    """
    task = async_validate
    
    def __init__(self, cohort_id):
        """
        Initialize validation, set metadata
        
        Parameters:
            cohort_id   : an existing cohort with validated == False
        """
        self.cohort_id = cohort_id
    
    @classmethod
    def from_upload(cls, cohort_upload, owner_user_id):
        """
        Create a new cohort and validate a list of uploaded users for it
        
        Parameters:
            cohort_upload   : the cohort upload form, parsed by WTForms
            owner_user_id   : the Wikimetrics user id that is uploading
        
        Returns:
            An instance of ValidateCohort
        """
        cohort = Cohort(
            name=cohort_upload.name.data,
            description=cohort_upload.description.data,
            default_project=cohort_upload.project.data,
            enabled=True,
            public=False,
            validated=False,
        )
        session = db.get_session()
        try:
            session.add(cohort)
            session.commit()
            
            cohort_user = CohortUser(
                user_id=owner_user_id,
                cohort_id=cohort.id,
                role=CohortUserRole.OWNER
            )
            session.add(cohort_user)
            session.commit()
            
            session.execute(
                WikiUser.__table__.insert(), [
                    {
                        'mediawiki_username': record['username'],
                        'project'           : record['project'],
                        'valid'             : None,
                        'reason_invalid'    : '',
                        'validating_cohort' : cohort.id,
                    } for record in cohort_upload.records
                ]
            )
            session.commit()
            return cls(cohort.id)
        except:
            return None
        finally:
            session.close()
    
    def run(self):
        session = db.get_session()
        try:
            cohort = session.query(Cohort).get(self.cohort_id)
            cohort.validation_queue_key = current_task.request.id
            session.commit()
            self.validate_records(session, cohort)
        finally:
            session.close()
    
    def validate_records(self, session, cohort):
        """
        Fetches the wiki_user(s) already added for self.cohort_id and validates
        their mediawiki_username against their stated project as either a user_id
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
            WikiUser.__table__.update().values(valid=None).where(
                WikiUser.validating_cohort == cohort.id
            )
        )
        session.commit()
        
        wikiusers = session.query(WikiUser) \
            .filter(WikiUser.validating_cohort == cohort.id) \
            .all()
        
        deduplicated = deduplicate_by_key(
            wikiusers,
            lambda r: (r.mediawiki_username, r.project)
        )
        
        flush = 0
        for wu in deduplicated:
            # flush bunches of records to update the UI but not kill performance
            flush += 1
            if flush > 500:
                flush = 1
                session.commit()
            
            try:
                normalized_project = normalize_project(wu.project)
                
                if normalized_project is None:
                    wu.reason_invalid = 'invalid project: {0}'.format(wu.project)
                    wu.valid = False
                    continue
                
                normalized_user = normalize_user(
                    wu.mediawiki_username,
                    normalized_project
                )
                if normalized_user is None:
                    wu.reason_invalid = 'invalid user_name / user_id: {0}'.format(
                        wu.mediawiki_username
                    )
                    wu.valid = False
                    continue
                
                wu.project = normalized_project
                wu.mediawiki_userid, wu.mediawiki_username = normalized_user
                wu.valid = True
            except:
                continue
        session.commit()
        
        unique_and_validated = deduplicate_by_key(
            deduplicated,
            lambda r: (r.mediawiki_username, r.project)
        )
        
        session.execute(
            CohortWikiUser.__table__.insert(), [
                {
                    'cohort_id'     : cohort.id,
                    'wiki_user_id'  : wu.id,
                } for wu in unique_and_validated
            ]
        )
        
        # clean up any duplicate wiki_user records
        session.execute(WikiUser.__table__.delete().where(and_(
            WikiUser.validating_cohort == cohort.id,
            WikiUser.id.notin_([wu.id for wu in unique_and_validated])
        )))
        cohort.validated = True
        session.commit()
    
    def __repr__(self):
        return '<ValidateCohort("{0}")>'.format(self.cohort_id)


def normalize_project(project):
    project = project.strip().lower()
    if project in db.project_host_map:
        return project
    else:
        # try adding wiki to end
        new_proj = project + 'wiki'
        if new_proj not in db.project_host_map:
            return None
        else:
            return new_proj


def normalize_user(user_name_or_id, project):
    mediawiki_user = get_mediawiki_user_by_name(user_name_or_id, project)
    if mediawiki_user is not None:
        return (mediawiki_user.user_id, mediawiki_user.user_name)
    
    if not user_name_or_id.isdigit():
        return None
    
    mediawiki_user = get_mediawiki_user_by_id(user_name_or_id, project)
    if mediawiki_user is not None:
        return (mediawiki_user.user_id, mediawiki_user.user_name)
    
    return None


def get_mediawiki_user_by_name(username, project):
    session = db.get_mw_session(project)
    try:
        return session.query(MediawikiUser)\
            .filter(MediawikiUser.user_name == username)\
            .one()
    except (MultipleResultsFound, NoResultFound):
        return None
    finally:
        session.close()


def get_mediawiki_user_by_id(id, project):
    session = db.get_mw_session(project)
    try:
        return session.query(MediawikiUser)\
            .filter(MediawikiUser.user_id == id)\
            .one()
    except (MultipleResultsFound, NoResultFound):
        return None
    finally:
        session.close()
