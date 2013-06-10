from database import get_mw_session
import job
from query_job import QueryJob
from queue import celery

__all__ = [
    'MutliProjectQueryJob',
]

class MultiProjectQueryJob(job.JobNode):
    def __init__(self, cohort, metric):
        super(MultiProjectQueryJob, self).__init__()
        self.cohort = cohort
        self.metric = metric
        
        self.children = []
        for project, user_ids in cohort.group_by_project():
            session = get_mw_session(project)
            # note that user_ids is actually just an iterator
            self.children.append(QueryJob(user_ids, session))


    @celery.task
    def finish(query_results):
        return reduce(dict.update, query_results, {})
