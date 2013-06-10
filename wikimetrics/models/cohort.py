import itertools
from operator import itemgetter
from sqlalchemy import Column, Integer, Boolean, DateTime, String
from wikimetrics.database import Base, Session
# TODO: there has to be a more elegant way of importing this
from .wikiuser import WikiUser
from .cohort_wikiuser import CohortWikiUser

__all__ = [
    'Cohort',
]

class Cohort(Base):
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
        session = Session()
        tuples_with_ids = session\
            .query(WikiUser.mediawiki_userid)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == self.id)\
            .all()
        return (t[0] for t in tuples_with_ids)


    def group_by_project(self):
        session = Session()
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
