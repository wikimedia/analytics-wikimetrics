from sqlalchemy import Column, Integer, String
from wikimetrics.database import db

__all__ = [
    'WikiUser',
]

class WikiUser(db.WikimetricsBase):
    """
    This class represents mediawiki users which compose
    cohorts.  A user is defined as a username or user_id
    along with the project name on which that user registered.
    This class is mapped to the wiki_user table using
    sqlalchemy.declarative
    """
    
    
    __tablename__ = 'wiki_user'
    
    id = Column(Integer, primary_key=True)
    mediawiki_username = Column(String(50))
    mediawiki_userid = Column(Integer(50))
    project = Column(String(45))
    
    def __repr__(self):
        return '<WikiUser("{0}")>'.format(self.id)
