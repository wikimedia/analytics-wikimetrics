import itertools
from operator import itemgetter
from sqlalchemy import Column, Integer, Boolean, DateTime, String
from wikimetrics.configurables import db
# TODO: there has to be a more elegant way of importing this
from .wikiuser import WikiUser
from .cohort_wikiuser import CohortWikiUser

__all__ = [
    'Cohort',
]

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
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(254))
    default_project = Column(String(50))
    created = Column(DateTime)
    changed = Column(DateTime)
    enabled = Column(Boolean)
    public = Column(Boolean, default=False)
    
    
    def __repr__(self):
        return '<Cohort("{0}")>'.format(self.id)
    
    
    def __iter__(self):
        """ returns list of user_ids """
        session = db.get_session()
        tuples_with_ids = session\
            .query(WikiUser.mediawiki_userid)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == self.id)\
            .all()
        return (t[0] for t in tuples_with_ids)
    
    
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
        
        session = db.get_session()
        user_id_projects = session\
            .query(WikiUser.mediawiki_userid, WikiUser.project)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == self.id)\
            .order_by(WikiUser.project)\
            .all()
        # TODO: push this logic into sqlalchemy.  The solution
        # includes subquery(), but I can't seem to get anything working
        groups = itertools.groupby(user_id_projects, key=itemgetter(1))

        # note: the below line is more concise but harder to read
        #return ((project, (r[0] for r in users)) for project, users in groups)
        for project, users in groups:
            yield project, (r[0] for r in users)
