from sqlalchemy import Column, Integer, ForeignKey
from wikimetrics.configurables import db

__all__ = [
    'CohortWikiUser',
]

class CohortWikiUser(db.WikimetricsBase):
    """
    Represents the join table between `cohort` and `wiki_user`
    tables.  Uses sqlalchemy.declarative to handle db mapping
    """
    
    __tablename__ = 'cohort_wiki_user'
    
    id = Column(Integer, primary_key=True)
    wiki_user_id = Column(Integer(50), ForeignKey('wiki_user.id'))
    cohort_id = Column(Integer(50), ForeignKey('cohort.id'))
    
    def __repr__(self):
        return '<CohortWikiUser("{0}")>'.format(self.id)

