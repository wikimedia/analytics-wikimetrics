import collections
from sqlalchemy import Column, Integer, String, ForeignKey
from wikimetrics.database import Base
from celery import group, chord

__all__ = [
    'Job',
    'JobNode',
    'JobLeaf',
]

class JobStatus(object):
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
        self.user_id = 1#TODO: get_user_id()
        self.status = JobStatus.CREATED
        self.parent_job_id = parent_job_id
        self.result_id = None
    
    def __repr__(self):
        return '<Job("{0}")>'.format(self.id)
    
    def get_classpath(self):
        return str(type(self))
    
    def get_user_id(self):
        return 'TODO: get user id from flask session'

class JobNode(Job):
    def __init__(self, cohort, metrics):
        super(JobNode, self).__init__()
    
    def __call__(self):
        child_task_group = group(child.subtask() for child in self.children)
        chord(child_task_group, self.finish).apply_async()
    
    def finish(self):
        pass

class JobLeaf(Job):
    def __init__(self, cohort, metrics):
        super(JobLeaf, self).__init__()
