import time
import celery
from celery import group, chord, current_task
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from celery.contrib.methods import task_method
from flask.ext.login import current_user
from wikimetrics.configurables import db, queue
from ..persistent_report import PersistentReport


__all__ = [
    'Report',
    'ReportNode',
    'ReportLeaf',
]


"""
We use a tree-based report model to represent the relationships
between tasks which have a partial ordering, but which should
still be loosely coupled or asynchronous.  For example, if we want
to compute the average of some metric for a cohort, it makes sense
to first compute the metric for each user and then take the average.
In this example both steps would Reports, and the averaging task would
register the task of computing the actual metric as its child.

Specifically, we distinguish between `ReportLeaf` instances, which have no
subreports, and `ReportNode` isntances, which require their children to be
excecuted first, before carrying out their task.  Computing a simple
metric would be a `ReportLeaf`, whereas any aggregator would be a `ReportNode`
"""


task_logger = get_task_logger(__name__)


class Report(object):
    
    show_in_ui = False
    
    def __init__(self,
                 user_id=None,
                 status=celery.states.PENDING,
                 name=None,
                 result_key=None,
                 children=[],
                 parameters='{}'):
        
        self.user_id = user_id
        if not self.user_id:
            try:
                if current_user.is_authenticated():
                    self.user_id = current_user.id
            except RuntimeError:
                # nothing to worry about, just using current_user outside
                # of a web context.  This should only happen during testing
                pass
        
        self.status = status
        self.name = name
        self.result_key = result_key
        self.children = children
        
        # store report to database
        # note that result_key is always empty at this stage
        pj = PersistentReport(user_id=self.user_id,
                              status=self.status,
                              name=self.name,
                              show_in_ui=self.show_in_ui,
                              parameters=parameters)
        db_session = db.get_session()
        db_session.add(pj)
        db_session.commit()
        self.persistent_id = pj.id
    
    def __repr__(self):
        return '<Report("{0}")>'.format(self.persistent_id)
    
    def set_status(self, status, task_id):
        """
        helper function for updating database status after celery
        task has been started
        """
        db_session = db.get_session()
        pj = db_session.query(PersistentReport).get(self.persistent_id)
        pj.status = status
        pj.result_key = task_id
        db_session.add(pj)
        db_session.commit()
    
    @queue.task(filter=task_method)
    def task(self):
        # NOTE: ReportNode can not override this special celery-decorated instance method
        if not isinstance(self, ReportNode):
            self.set_status(celery.states.STARTED, task_id=current_task.request.id)
        result = self.run()
        return result
    
    def run(self):
        """
        each report subclass should implement this method to do the
        meat of the task.  The return type can be anything"""
        pass


class ReportNode(Report):
    
    def child_tasks(self):
        return group(child.task.s() for child in self.children)
    
    def run(self):
        if self.children:
            # this is a hack to get around the fact that celery can't deal with
            # instance methods as the final callback on a chord
            # instead, we pass self in as an argument, and the actual
            # list of results from the child tasks are prepended to the args
            # with which finish_task is actually invoked
            header = self.child_tasks()
            callback = self.finish_task.s(self)
            children_then_finish = chord(header)(callback)
            task_logger.info('running task: %s', current_task.request.id)
            return children_then_finish
        else:
            return []
    
    @queue.task(filter=task_method)
    def finish_task(results, self):
        """
        This is the task which is executed after all of the child tasks
        in a ReportNode have been executed.  It serves as a wrapper to the
        finish() method which actually deals with child task results.
        Note that the signature of this method is a little funny due to
        a hack to get around the way that celery handles instance method tasks.
        The ReportNode instance (self) is specified  when the callback
        subtask is created, and the results argument is filled in by celery
        once they have completed.  The order is just reversed because celery
        is hardcoded to prepend the results from a chord into the argument list
        specified when createing the subtask.
        """
        self.set_status(celery.states.STARTED, task_id=current_task.request.id)
        result = self.finish(results)
        return result
    
    def finish(self, results):
        """
        Each ReportNode sublcass should implement this method to
        deal with the results of its child reports"""
        pass


class ReportLeaf(Report):
    pass
