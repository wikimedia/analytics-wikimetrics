import collections
from sqlalchemy import Column, Integer, String, ForeignKey
from wikimetrics.database import Base
from queue import celery
from celery import group, chord

__all__ = [
    'Job',
    'JobNode',
    'JobLeaf',
    'JobStatus',
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
    status = Column(String(100), default=JobStatus.CREATED)
    result_id = Column(String(50))
    
    
    # FIXME: calling ConcatMetricsJob().run uses this run instead of the JobNode one
    #@celery.task
    #def run(self):
        #pass
    
    def __repr__(self):
        return '<Job("{0}")>'.format(self.id)
    
    def get_classpath(self):
        return str(type(self))

class JobNode(Job):
    
    def child_tasks(self):
        return group(child.run.s(child) for child in self.children)
    
    @celery.task
    def run(self):
        children_then_finish = chord(self.child_tasks())(self.finish.s())
        children_then_finish.get()
    
    @celery.task
    def finish(self):
        pass

class JobLeaf(Job):
    pass
