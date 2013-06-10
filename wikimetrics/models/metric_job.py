import job
from queue import celery
from wikimetrics.database import get_mw_session

__all__ = [
    'MetricJob',
]

class MetricJob(job.JobLeaf):
    def __init__(self, metric, user_ids, project):
        self.metric = metric
        self.user_ids = user_ids
        self.project = project
    
    @celery.task
    def run(self):
        session = get_mw_session(self.project)
        return self.metric(self.user_ids, session)
