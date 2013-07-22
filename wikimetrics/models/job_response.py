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
    
    show_in_ui = False
    
    def __init__(self, cohort_metrics_jobs, *args, **kwargs):
        """
        Parameters:
        
            cohort_metrics [(Cohort, Metric),...]  : list of cohort-metric pairs to be run
        """
        super(JobResponse, self).__init__(*args, **kwargs)
        self.children = cohort_metrics_jobs
    
    def finish(self, job_results):
        return job_results
    
    def __repr__(self):
        return '<JobResponse("{0}")>'.format(self.persistent_id)
