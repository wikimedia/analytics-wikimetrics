import job
from queue import celery
import pprint
from metric_job import MetricJob

__all__ = [
    'ConcatMetricsJob',
]

class ConcatMetricsJob(job.JobNode):
    def __init__(self, cohort, metrics):
        super(ConcatMetricsJob, self).__init__()
        self.cohort = cohort
        self.metrics = metrics
        # TODO enforce children always have a run @celery.task
        self.children = [MetricJob(cohort, metric) for metric in metrics]
        # TODO self.save()
    
    ## NOTE: this will be used by celery if we implement it, so we must take care
    #def __reduce__(self):
        ## TODO: pickle self.cohort and self.metrics
        #pass
    
    def from_db(job_id):
        # TODO: get job, create cohort and metrics
        return ConcatMetricsJob(cohort, metrics)
    
    @celery.task
    def finish(query_results):
        # we're done - record result
        for result in query_results:
            pprint.pprint(result)
