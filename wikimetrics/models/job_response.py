from celery.contrib.methods import task_method
from wikimetrics.configurables import queue
import job
from .multi_project_metric_job import MultiProjectMetricJob

__all__ = [
    'JobResponse',
]


class JobResponse(job.JobNode):
    """
    Represents a batch of cohort-metric jobs created by the 
    user during a single jobs/create/ workflow.  This is also
    intended to be the unit of work which could be easily re-run.
    """
    
    
    def __init__(self, cohort_metrics,*args, **kwargs):
        """
        Parameters:
        
            cohort_metrics [(Cohort, Metric),...]  : list of cohort-metric pairs to be run
        """
        super(JobResponse, self).__init__(*args, **kwargs)
        self.children = [MultiProjectMetricJob(c, m) for c, m in cohort_metrics]
    
    @queue.task(filter=task_method)
    def finish(job_results):
        return job_results
