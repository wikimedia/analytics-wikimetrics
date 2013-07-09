import collections
import pickle
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from celery import group, chord
from celery.utils.log import get_task_logger
from celery import current_task
from celery.contrib.methods import task_method
import traceback
import logging

from wikimetrics.configurables import db, queue

__all__ = [
    'Job',
    'JobNode',
    'JobLeaf',
    'JobStatus',
    'PersistentJob'
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



task_logger = get_task_logger(__name__)
sh = logging.StreamHandler()
task_logger.addHandler(sh)


class JobStatus(object):
    CREATED  = 'CREATED'
    STARTED  = 'STARTED'
    FINISHED = 'FINISHED'

class PersistentJob(db.WikimetricsBase):
    __tablename__ = 'job'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    result_key = Column(String(50)) 
    status = Column(String(50))


class Job(object):
    
    def __init__(self,
            user_id=None,
            status=JobStatus.CREATED,
            result_id=None,
            children=[]):
        self.user_id = user_id
        self.status = status
        self.result_id = result_id
        self.children = children
    
    def __repr__(self):
        return '<Job("{0}")>'.format(self.id)
    
    def run(self):
        """
        each job subclass should implement this method to do the
        meat of the task.  The return type can be anything"""
        pass


class JobNode(Job):
    
    def child_tasks(self):
        return group(child.run.s(child) for child in self.children)
    
    @queue.task(filter=task_method)
    def run(self):
        try:
            if self.children:
                children_then_finish = chord(self.child_tasks())(self.finish.s())
                task_logger.info('created chord')
                children_then_finish.get()
                task_logger.info('got chord result: %s', children_then_finish.result)
                return children_then_finish.result
            else:
                return []
        except:
            task_logger.exception('caught exception within worker:')
            raise
    
    @queue.task(filter=task_method)
    def finish(results):
        pass


class JobLeaf(Job):
    pass
