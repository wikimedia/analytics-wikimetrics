import collections
import pickle
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from celery import group, chord
from celery.utils.log import get_task_logger
from celery import current_task
import traceback
import logging

from wikimetrics.configurables import db, queue

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



task_logger = get_task_logger(__name__)
sh = logging.StreamHandler()
task_logger.addHandler(sh)


class JobStatus(object):
    CREATED  = 'CREATED'
    STARTED  = 'STARTED'
    FINISHED = 'FINISHED'


class Dammy(db.WikimetricsBase):
    __tablename__ = 'dummy'
    id = Column(Integer, primary_key=True)
    def __init__(self, job):
        self.job = job
    @queue.task
    def rando_taks(self):
        pass

# this method needs to be at module level for pickling purposes
def from_db(job_id):
    """
    All `Job` subclasses should implement this to ensure that they
    can be resumed from the database
    
    Parameters:
        job_id  : primary key in the job table which can be used to
                  locate the serialized information with which a new job
                  can be created
    
    Returns:
        a new instance of the Job() class which can be re-run
    """
    print 'calling from_db!'
    session = db.get_session()
    job = session.query(Job).get(job_id)
    # note the cast to str is necessary because by default
    # sqlalchemy returns unicode, which changes the byte representation
    state_dict = pickle.loads(str(job.state))
    job.__dict__.update(state_dict)
    return job


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
    state = Column(String(1000))
    status = Column(String(100), default=JobStatus.CREATED)
    result_id = Column(String(50))
    #parent_id = Column(Integer, ForeignKey('job.id'))
    #children = relationship('Job')
            #backref=backref("parent", remote_side='job.id'))
    
    # FIXME: calling ConcatMetricsJob().run uses this run instead of the JobNode one
    #@queue.task
    #def run(self):
        #pass
    
    def get_state_dict(self):
        """
        All `Job` subclasses should implement this to ensure that any non-
        database-mapped attributes are saved and reloaded during pickle
        serialization.  The workflow goes as follows:
            
            1) upon calling job.delay(), the job.__reduce__() function is called
            2) job.__reduce__() calls job.save()
            3) job.save() calls job.get_state_dict()
            4) job.save() stores state_dict to db-mapped attribute job.state
            5) job.__reduce__() returns job.from_db() and job.id
                   as the unpickling function and state, respectively
            6) job.from_db() is called on unpickling end
            7) job.from_db() gets new job object from db using job_id
            8) job.from_db() updates job object using db.state with:
                   job.__dict__.update(str(pickle.loads(job.state)))
            9) job.from_db() returns new job to be used in celery context
        """
        return {}
    
    def save(self):
        
        state_dict = self.get_state_dict()
        self.state = pickle.dumps(state_dict)
        session = db.get_session()
        session.add(self)
        session.commit()
    
    def __reduce__(self):
        self.save()
        return(from_db, (self.id,))
    
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
    
    @queue.task(serializer='pickle')
    def run(self):
        with open('celery_log_{0}.log'.format(current_task.request.id), 'w') as fout:
            fout.write('trace_back at run()r:\n%s' % traceback.format_stack())
            try:
                children_then_finish = chord(self.child_tasks())(self.finish.s())
                children_then_finish.get()
            except:
                task_logger.exception('caught exception within worker:')
                fout.write('caught exception within worker:\n{0}'.format(traceback.format_exc()))
    
    @queue.task
    def finish(self):
        pass


class JobLeaf(Job):
    pass
