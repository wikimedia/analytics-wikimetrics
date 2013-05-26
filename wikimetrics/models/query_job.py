import job

class QueryJob(job.Job):
    def __init__(self, cohort, metric, parent_job_id):
        self.cohort = cohort
        self.metric = metric
        self.parent_job_id = parent_job_id
    
    def __call__(self):
        super(job.Job, self).__call__()
