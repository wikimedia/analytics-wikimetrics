from sqlalchemy import Column, Integer, String, ForeignKey

from usermetrics.database import Base

import collections

class JobStatus:
    CREATED = 'CREATED'
    STARTED = 'STARTED'
    FINISHED = 'FINISHED'

class Job(Base):
    __tablename__ = 'job'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    classpath = Column(String(200))
    status = Column(String(100))
    result_id = Column(String(50))
    
    def __init__(self, parent_job_id=None):
        self.user_id = get_user_id()
        self.classpath = get_classpath()
        self.status = JobStatus.CREATED
        self.parent_job_id = parent_job_id
        self.result_id = None
    
    def __repr__(self):
        return '<Job("{0}")>'.format(self.id)
    
    def __call__(self):
        child_group = celery.Group(self.children)
        celery.Chord(child_group, self.finish).apply_async()
    
    def get_classpath(self):
        return str(type(self))
    
    def get_user_id(self):
        return 'TODO: get user id from flask session'
