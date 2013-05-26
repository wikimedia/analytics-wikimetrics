import job
import celery

__all__ = [
    'QueryJob',
]

class QueryJob(job.JobLeaf):
    def __init__(self, cohort, metric):
        self.cohort = cohort
        self.metric = metric
    
    def __call__(self):
        super(QueryJob, self).__call__()
        return self.metric(self.cohort)

# TODO: class decorator
QueryJob.Task = celery.task(QueryJob)
