import job
import celery
import pprint
from query_job import QueryJob

__all__ = [
    'ConcatMetricsJob',
]

@celery.task
class ConcatMetricsJob(job.JobNode):
    def __init__(self, cohort, metrics):
        super(job.JobNode, self).__init__()
        self.cohort = cohort
        self.metrics = metrics
        # Make sure that children are always Celery tasks with parameterless __call__
        self.children = [QueryJob(cohort, metric) for metric in metrics]
        # TODO self.save()
    
    def __reduce__(self):
        # TODO: pickle self.cohort and self.metrics
        pass
    
    def from_db(job_id):
        # TODO: get job, create cohort and metrics
        return ConcatMetricsJob(cohort, metrics)
    
    def __call__(self):
        super(job.JobNode, self).__call__()
    
    @celery.task
    def finish(self, *query_results):
        super(job.JobNode, self).finish()
        # we're done - record result
        for result in query_results:
            pprint.pprint(result)
        self.status = JobStatus.FINISHED
