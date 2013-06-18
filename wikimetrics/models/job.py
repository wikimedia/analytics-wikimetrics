import collections
from sqlalchemy import Column, Integer, String, ForeignKey
from celery import group, chord

from wikimetrics.configurables import db
from queue import celery

__all__ = [
    'Job',
    'JobNode',
    'JobLeaf',
    'JobStatus',
]

"""
We use a tree-based job model to represent the relationships 
between tasks which have a partial ordering, but which should
still be loosely coupled or asynchronous.  For example, if we want
to compute the average of some metric for a cohort, it makes sense
to first compute the metric for each user and then take the average.
In this example both steps would Jobs, and the averaging task would
register the task of computing the actual metric as its child.

Specifically, we distinguish between `JobLeaf` instances, which have no
subjobs, and `JobNode` isntances, which require their children to be
excecuted first, before carrying out their task.  Computing a simple
metric would be a `JobLeaf`, whereas any aggregator would be a `JobNode`
"""


class JobStatus(object):
    CREATED = 'CREATED'
    STARTED = 'STARTED'
    FINISHED = 'FINISHED'

class Job(db.WikimetricsBase):
    """
    Base class for all jobs.  Uses sqlalchemy.declarative to
    map instance to `job` table.  This means that the database can be used
    as a central server for persistent job status info.  Jobs are also
    intended to be re-runnable from a serialized representation, using
    the Job.from_db alternate constructor.
    """
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
    
    @classmethod
    def from_db(cls, job_id):
        """
        All `Job` subclasses should implement this to ensure that they
        can be resumed from the database
        
        Parameters:
            cls     : from_db is a class_method so it requires a class
                      istance as it's first arg, so that it can be called
                      with JobSubclass.form_db(job_id)
            job_id  : primary key in the job table which can be used to
                      locate the serialized information with which a new job
                      can be created
        
        Returns:
            a new instance of the Job() class which can be re-run
        """
        pass

    def __repr__(self):
        return '<Job("{0}")>'.format(self.id)
    
    def get_classpath(self):
        return str(type(self))
    
    def run(self):
        """
        each job subclass should implement this method to do the
        meat of the task.  The return type can be anything"""
        pass

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
