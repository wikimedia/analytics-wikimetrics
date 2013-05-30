from sqlalchemy import Column, Integer, String
from wikimetrics.database import Base

class WikiUser(Base):
    __tablename__ = 'wiki_user'
    
    id = Column(Integer, primary_key=True)
    mediawiki_username = Column(String(50))
    mediawiki_userid = Column(Integer(50))
    project = Column(String(45))
    
    def __init__(self,
            mediawiki_username = None,
            mediawiki_userid = None,
            project = None):
        """TODO: make this class accept either a username OR user_id"""
        self.mediawiki_username = mediawiki_username
        self.mediawiki_userid = mediawiki_userid
        self.project = project
    
    def __repr__(self):
        return '<WikiUser("{0}")>'.format(self.id)
