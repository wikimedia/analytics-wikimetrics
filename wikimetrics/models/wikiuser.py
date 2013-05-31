from sqlalchemy import Column, Integer, String
from wikimetrics.database import Base

__all__ = [
    'WikiUser',
]

class WikiUser(Base):
    __tablename__ = 'wiki_user'
    
    id = Column(Integer, primary_key=True)
    mediawiki_username = Column(String(50))
    mediawiki_userid = Column(Integer(50))
    project = Column(String(45))
    
    def __repr__(self):
        return '<WikiUser("{0}")>'.format(self.id)
