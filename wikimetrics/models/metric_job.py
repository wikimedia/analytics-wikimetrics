import job
from celery.contrib.methods import task_method
from wikimetrics.configurables import queue, db

__all__ = [
    'MetricJob',
]


class MetricJob(job.JobLeaf):
    """
    Job type responsbile for running a single metric on a project-
    homogenous list of user_ids.  Like all jobs, the database session
    is constructed within MetricJob.run()
    """
    
    def __init__(self, metric, user_ids, project):
        super(MetricJob, self).__init__()
        self.metric = metric
        self.user_ids = list(user_ids)
        self.project = project
    
    @queue.task(filter=task_method)
    def run(self, *args):
        session = db.get_mw_session(self.project)
        return self.metric(self.user_ids, session)
