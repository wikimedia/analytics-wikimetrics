from sqlalchemy import Column, Integer
from wikimetrics.database import Base

__all__ = [
    'CohortWikiUser',
]

class CohortWikiUser(Base):
    __tablename__ = 'cohort_wiki_user'

    id = Column(Integer, primary_key=True)
    wiki_user_id = Column(Integer(50))
    cohort_id = Column(Integer(50))

    def __repr__(self):
        return '<CohortWikiUser("{0}")>'.format(self.id)

