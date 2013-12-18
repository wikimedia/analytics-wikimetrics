import itertools
from operator import itemgetter
from sqlalchemy import Column, Integer, Boolean, DateTime, String, func

from wikimetrics.utils import Unauthorized
from wikimetrics.configurables import db
from wikiuser import WikiUser
from cohort_wikiuser import CohortWikiUser
from cohort_user import CohortUser, CohortUserRole
from user import User


__all__ = ['Cohort']


class Cohort(db.WikimetricsBase):
    """
    This class represents a list of users along with the project
    on which their username exists.  Using sqlalchemy.declarative
    It maps to the cohort table  which keeps metadata about the cohort,
    however it is also home to a variety of conveneince functions
    for interacting with the actual list of users in that cohort.
    
    Importantly, there is no guarantee that a cohort consist of users
    from a single project.  To get the set of all users associated with
    a single project within a cohort use Cohort.group_by_project.
    """
    
    __tablename__ = 'cohort'
    
    id                      = Column(Integer, primary_key=True)
    name                    = Column(String(50))
    description             = Column(String(254))
    default_project         = Column(String(50))
    created                 = Column(DateTime, default=func.now())
    changed                 = Column(DateTime)
    enabled                 = Column(Boolean)
    public                  = Column(Boolean, default=False)
    validated               = Column(Boolean, default=False)
    validate_as_user_ids    = Column(Boolean, default=True)
    validation_queue_key    = Column(String(50))
    
    def __repr__(self):
        return '<Cohort("{0}")>'.format(self.id)
    
    # TODO: that weird bug that makes "None" show up in metric results
    # starts with iterating Cohorts here
    def __iter__(self):
        """ returns list of user_ids """
        db_session = db.get_session()
        try:
            wikiusers = self.filter_wikiuser_query(
                db_session.query(WikiUser.mediawiki_userid)
            ).all()
        finally:
            db_session.close()
        return (r.mediawiki_userid for r in wikiusers)
    
    def group_by_project(self):
        """
        mimics the interface of itertools.groupby, with the
        exception that the grouped items are simply user_ids
        rather than complete user records
        
        Returns:
            iterable of tuples of the form:
                (project, <iterable_of_usernames>)
        
        this is useful for turning a project-heterogenous cohort
        into a set of project-homogenous cohorts, which can be
        analyzed using a single database connection
        """
        db_session = db.get_session()
        try:
            user_id_projects = self.filter_wikiuser_query(
                db_session.query(WikiUser.mediawiki_userid, WikiUser.project)
            ).order_by(WikiUser.project).all()
        finally:
            db_session.close()
        # TODO: push this logic into sqlalchemy.  The solution
        # includes subquery(), but I can't seem to get anything working
        groups = itertools.groupby(user_id_projects, key=itemgetter(1))
        
        return (
            (project or self.default_project, (r[0] for r in users))
            for project, users in groups
        )
    
    def filter_wikiuser_query(self, wikiusers_query):
        """
        Parameters:
            wikiusers_query : a sqlalchemy query object asking for one or more
                                properties of WikiUser
        
        Return:
            the query object passed in, filtered and joined to the
            appropriate tables, and restricted to this cohort
        """
        return wikiusers_query\
            .join(CohortWikiUser)\
            .join(Cohort)\
            .filter(Cohort.id == self.id)\
            .filter(Cohort.validated)\
            .filter(WikiUser.valid)
    
    @staticmethod
    def get_safely(db_session, user_id, by_id=None, by_name=None):
        """
        Gets a cohort but first checks permissions on it
        
        Parameters
            db_session  : the database session to query
            user_id     : the user that should have access to the cohort
            by_id       : the cohort id to get.  <by_id> or <by_name> is True
            by_name     : the cohort name to get.  <by_id> or <by_name> is True
        
        Returns
            If found, a Cohort instance with id == cohort_id or name == cohort_name
        
        Raises
            NoResultFound   : cohort did not exist
            Unauthorized    : user_id is not allowed to access this cohort
        """
        query = db_session.query(Cohort, CohortUser.role)\
            .join(CohortUser)\
            .join(User)\
            .filter(User.id == user_id)\
            .filter(Cohort.enabled)
        
        if not by_id is None:
            query = query.filter(Cohort.id == by_id)
        if not by_name is None:
            query = query.filter(Cohort.name == by_name)
        
        cohort, role = query.one()
        if role in CohortUserRole.SAFE_ROLES:
            return cohort
        else:
            raise Unauthorized('You are not allowed to use this cohort')
