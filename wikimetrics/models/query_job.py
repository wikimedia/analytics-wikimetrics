import job
import celery

__all__ = [
    'QueryJob',
]

class QueryJob(job.JobLeaf):
    def __init__(self, cohort, metric):
        self.cohort = cohort
        self.metric = metric
    
    @celery.task
    def run(self):
        return self.metric(self.cohort)
