import collections
import pickle
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
import celery
from celery import group, chord
from celery.utils.log import get_task_logger
from celery import current_task
from celery.contrib.methods import task_method
import traceback
import logging
import time

from wikimetrics.configurables import db, queue

__all__ = [
    'Job',
    'JobNode',
    'JobLeaf',
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


class PersistentJob(db.WikimetricsBase):
    __tablename__ = 'job'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    result_key = Column(String(50)) 
    status = Column(String(50))


class Job(object):
    
    def __init__(self,
            user_id=None,
            status=celery.states.PENDING,
            result_key=None,
            children=[]):
        self.user_id = user_id
        self.status = status
        self.result_key = result_key
        self.children = children
        
        # create PersistentJob and store id
        # note that result_key is always empty at this stage
        pj = PersistentJob(user_id=self.user_id,
                status=self.status)
        session = db.get_session()
        session.add(pj)
        session.commit()
        self.persistent_id = pj.id
    
    def __repr__(self):
        return '<PersistentJob("{0}")>'.format(self.persistent_id)
    
    def set_status(self, status, task_id):
        """
        helper function for updating database status after celery
        task has been started
        """
        db_session = db.get_session()
        pj = db_session.query(PersistentJob).get(self.persistent_id)
        pj.status = status
        pj.result_key = task_id
        db_session.add(pj)
        db_session.commit()
    
    @queue.task(filter=task_method)
    def task(self):
        self.set_status(celery.states.STARTED, task_id=current_task.request.id)
        task_logger.info('starting task: %s', current_task.request.id)
        result = self.run()
        return result
    
    def run(self):
        """
        each job subclass should implement this method to do the
        meat of the task.  The return type can be anything"""
        pass


class JobNode(Job):
    
    def child_tasks(self):
        return group(child.task.s() for child in self.children)
    
    def run(self):
        if self.children:
            children_then_finish = chord(self.child_tasks())(self.finish.s())
            children_then_finish.get()
            return children_then_finish.result
        else:
            return []
    
    def finish(results):
        pass


class JobLeaf(Job):
    pass
