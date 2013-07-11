from wikimetrics.configurables import queue
from celery.utils.log import get_task_logger
import logging
import job
from metric_job import MetricJob

__all__ = [
    'MultiProjectMetricJob',
]


class MultiProjectMetricJob(job.JobNode):
    """
    A job responsbile for running a single metric on a potentially
    project-heterogenous cohort. This just abstracts away the task
    of grouping the cohort by project and calling a MetricJob on
    each project-homogenous list of user_ids.
    """
    
    def __init__(self, cohort, metric, *args, **kwargs):
        super(MultiProjectMetricJob, self).__init__(*args, **kwargs)
        self.cohort = cohort
        self.metric = metric
        
        self.children = []
        for project, user_ids in cohort.group_by_project():
            # note that user_ids is actually just an iterator
            self.children.append(MetricJob(metric, user_ids, project))
    
    def finish(self, query_results):
        merged = {}
        for res in query_results:
            merged.update(res)
        return merged
