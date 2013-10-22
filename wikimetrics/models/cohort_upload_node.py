import celery
from celery.utils.log import get_task_logger
from flask.ext.login import current_user
from wikimetrics.configurables import app, db, queue
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import label, between, and_, or_
from ..utils import deduplicate_by_key
from wikimetrics.models import (
    MediawikiUser, Cohort, WikiUser
)
from pprint import pprint

__init__ = [
    'get_wikiuser_by_name',
    'get_wikiuser_by_id',
    'update_wu_invalid',
    'update_wu_valid',
]


# test
task_logger = get_task_logger(__name__)


@queue.task()
def async_validate(validate_cohort):
    task_logger.info("Running Cohort Validation job")
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
    
    def __init__(self, records, name, description, project):
        """
        Initialize validation, set metadata
        
        Parameters:
            cohort  : an existing cohort with validated == False
            records : a list of records as parsed from a CSV upload
        """
        self.records = records
        self.name = name
        self.description = description
        self.project = project
        self.create_cohort_and_dummy_wikiusers()
    
    @classmethod
    def fromupload(cls, cohort_upload):
        """
        Create a new cohort and validate a list of uploaded users for it
        
        Parameters:
            cohort_upload   : the cohort upload form, parsed by WTForms
        
        Returns:
            An instance of ValidateCohort
        """
        cohort = Cohort(
            name=cohort_upload.name,
            description=cohort_upload.description,
            default_project=cohort_upload.default_project,
            enabled=False,
            public=False,
            validated=False,
        )
        session = db.get_session()
        session.add(cohort)
        session.commit()
        
        #return cls(cohort, cohort_upload.records)
        return None
    
    #@classmethod
    #def fromcohort(cls, partial_cohort_upload):
        #"""
        #Using an existing cohort, reset all validation metadata and re-validate
        
        #Parameters:
            #partial_cohort_upload   : the cohort_id and user records, parsed by WTForms
        
        #Returns:
            #An instance of ValidateCohort
        #"""
        #session = db.get_session()
        #cohort = session.query(Cohort).get(partial_cohort_upload.cohort_id)
        
        #return cls(cohort, partial_cohort_upload.records)

    def create_cohort_and_dummy_wikiusers(self):
        session = db.get_session()
        new_cohort = Cohort(
            name=self.name,
            default_project=self.project,
            description=self.description,
            enabled=True,
        )
        self.cohort = new_cohort

        wikiusers = []
        session.bind.engine.execute(
            WikiUser.__table__.insert(), [
                {
                    "mediawiki_username": record["raw_username"],
                    "project": record["project"],
                    "valid": None,
                    "reason_invalid": "",
                } for record in self.records
            ]
        )
        session.add_all(wikiusers)
        session.commit()
    
    def validate_records(self):
        session = db.get_session()
        valid = []
        #invalid = []

        for record in self.records:
            normalized_project = normalize_project(record['project'])
            link_project = normalized_project or record['project'] or 'invalid'
            record['user_str'] = record['username']
            record['link'] = link_to_user_page(record['username'], link_project)
            if normalized_project is None:
                record['reason_invalid'] = 'invalid project: %s' % record['project']
                #invalid.append(record)
                update_wu_invalid(record)
                continue
            normalized_user = normalize_user(record['raw_username'], normalized_project)
            # make a link to the potential user page even if user doesn't exist
            # this gives a chance to see any misspelling etc.
            if normalized_user is None:
                app.logger.info(
                    'invalid user: {0} in project {1}'
                    .format(record['raw_username'], normalized_project)
                )
                record['reason_invalid'] = 'invalid user_name / user_id: {0}'.format(
                    record['raw_username']
                )
                #invalid.append(record)
                update_wu_invalid(record)
                continue
            # set the normalized values and append to valid
            record['project'] = normalized_project
            record['user_id'], record['username'] = normalized_user
            #valid.append(record)
            update_wu_valid(record)
        valid = deduplicate_by_key(valid, lambda r: (r['username'], r['project']))
        session.query(Cohort).filter(Cohort.id == self.cohort.id) \
               .update({"validated": True})
        session.commit()
    
    def run(self):
        self.validate_records()
    
    def __repr__(self):
        return 'ValidateCohort'


def update_wu_invalid(record):
    session = db.get_session()
    session.query(WikiUser) \
        .filter(or_(
            WikiUser.mediawiki_username == record['raw_username'],
            WikiUser.mediawiki_userid   == record['raw_username'])) \
        .update({
            "reason_invalid": record['reason_invalid'],
            "valid"         : False,
        })
    session.commit()
    session.close()


# TODO: naming change for get_wikiuser_by_name because it
# returns a MediawikiUser object and not WikiUser
def update_wu_valid(record):
    wu_by_name = get_wikiuser_by_name(record['raw_username'], record['project'])
    wu_by_uid  = get_wikiuser_by_id(record['raw_username'], record['project'])
    #wu = wu_by_name if wu_by_name is not None else wu_by_uid
    wu = wu_by_name or wu_by_uid
    if wu:
        session = db.get_session()
        session.query(WikiUser) \
            .filter(WikiUser.mediawiki_username == wu.user_name) \
            .update({
                "mediawiki_username": wu.user_name,
                "mediawiki_userid": wu.user_id,
                "valid"         : True,
            })
        session.commit()
        session.close()
    else:
        update_wu_invalid(record)


def project_name_for_link(project):
    if project.endswith('wiki'):
        return project[:len(project) - 4]
    return project


def get_wikiuser_by_name(username, project):
    db_session = db.get_mw_session(project)
    try:
        wikiuser = db_session.query(MediawikiUser)\
            .filter(MediawikiUser.user_name == username)\
            .one()
        db_session.close()
        return wikiuser
    except (MultipleResultsFound, NoResultFound):
        db_session.close()
        return None


def link_to_user_page(username, project):
    project = project_name_for_link(project)
    user_link = 'https://{0}.wikipedia.org/wiki/User:{1}'
    user_not_found_link = 'https://{0}.wikipedia.org/wiki/Username_could_not_be_parsed'
    # TODO: python 2 has insane unicode handling, switch to python 3
    try:
        return user_link.format(project, username)
    except UnicodeEncodeError:
        try:
            return user_link.format(project, username.encode('utf8'))
        except:
            return user_not_found_link.format(project)


def get_wikiuser_by_id(id, project):
    db_session = db.get_mw_session(project)
    try:
        wikiuser = db_session.query(MediawikiUser)\
            .filter(MediawikiUser.user_id == id)\
            .one()
        db_session.close()
        return wikiuser
    except (MultipleResultsFound, NoResultFound):
        db_session.close()
        return None


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


def normalize_user(user_str, project):
    wikiuser = get_wikiuser_by_name(user_str, project)
    if wikiuser is not None:
        return (wikiuser.user_id, wikiuser.user_name)
    
    if not user_str.isdigit():
        return None
    
    wikiuser = get_wikiuser_by_id(user_str, project)
    if wikiuser is not None:
        return (wikiuser.user_id, wikiuser.user_name)
    
    return None
