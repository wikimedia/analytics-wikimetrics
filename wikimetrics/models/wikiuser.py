from sqlalchemy import Column, Integer, String

from wikimetrics.database import Base

class WikiUser(Base):
    __tablename__ = 'wiki_user'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    user_id = Column(Integer(50))
    project = Column(String(45))
    
    def __init__(self, username, user_id, project):
        """TODO: make this class accept either a username OR user_id"""
        self.username = username
        self.user_id = user_id
        self.project = project
    
    def __repr__(self):
        return '<WikiUser("{0}","{1}", "{2}")>'.format(self.username, self.user_id, self.project)
