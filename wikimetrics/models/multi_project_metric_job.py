from ..database import get_mw_session
import job
from metric_job import MetricJob
from queue import celery

__all__ = [
    'MultiProjectMetricJob',
]

class MultiProjectMetricJob(job.JobNode):
    def __init__(self, cohort, metric):
        super(MultiProjectMetricJob, self).__init__()
        self.cohort = cohort
        self.metric = metric
        
        self.children = []
        for project, user_ids in cohort.group_by_project():
            session = get_mw_session(project)
            # note that user_ids is actually just an iterator
            self.children.append(MetricJob(metric, user_ids, session))


    @celery.task
    def finish(query_results):
        return reduce(dict.update, query_results, {})
