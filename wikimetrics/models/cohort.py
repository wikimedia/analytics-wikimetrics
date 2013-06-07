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
        return [t[0] for t in tuples_with_ids].__iter__()
