import pickle
from wikimetrics.configurables import queue, db
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
    
    
    def __init__(self, cohort_metrics, user_id):
        """
        Parameters:
        
            cohort_metrics [(Cohort, Metric),...]  : list of cohort-metric pairs to be run
        """
        super(JobResponse, self).__init__(user_id=user_id)
        self.children = [MultiProjectMetricJob(c, m) for c, m in cohort_metrics]
    
    def get_state_dict(self):
        """
        place any non-sqlalchemy attributes which need to be saved in this
        dict, and they will be pickled by sav() and unplicked by from_db(),
        using self.__dict__.update(pickle.loads(self.state))
        """
        return {'test_attr' : None}
    
    @queue.task
    def finish(job_results):
        return job_results
