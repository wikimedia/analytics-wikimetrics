import job
from queue import celery

__all__ = [
    'MetricJob',
]

class MetricJob(job.JobLeaf):
    def __init__(self, metric, user_ids, session):
        self.metric = metric
        self.user_ids = user_ids
        self.session = session
    
    @celery.task
    def run(self):
        return self.metric(self.user_ids, self.session)
