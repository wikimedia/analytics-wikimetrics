import collections
from sqlalchemy import Column, Integer, String, ForeignKey
from wikimetrics.database import Base
from setup import celery
from setup.celery import group, chord

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
        self.user_id = self.get_user_id()
        self.status = JobStatus.CREATED
        self.parent_job_id = parent_job_id
        self.result_id = None
    
    @celery.task
    def run(self):
        pass
    
    def __repr__(self):
        return '<Job("{0}")>'.format(self.id)
    
    def get_classpath(self):
        return str(type(self))
    
    def get_user_id(self):
        return 'TODO: get user id from flask session'

class JobNode(Job):
    def __init__(self):
        super(JobNode, self).__init__()
    
    def child_tasks(self):
        return group(child.run.subtask() for child in self.children)
    
    @celery.task
    def run(self):
        aggregator_task = chord(child_tasks(), self.finish.subtask())
        return aggregator_task.get()
    
    @celery.task
    def finish(self):
        pass

class JobLeaf(Job):
    def __init__(self):
        super(JobLeaf, self).__init__()
