import job
import job

@celery.task()
class ConcatMetricsJob(job.Job):
    def __init__(self, cohort, metrics):
        super(job.Job, self).__init__()
        self.cohort = cohort
        self.metrics = metrics
        self.children = [QueryJob(cohort, metric) for metric in metrics]
        self.save()
    
    def __reduce__(self):
        # TODO: pickle self.cohort and self.metrics
    
    def from_db(job_id)
        # TODO: get job, create cohort and metrics
        return ConcatMetricsJob(cohort, metrics)
    
    def __call__(self):
        super(job.Job, self).__call__()
    
    @celery.task()
    def finish(self):
        super(job.Job, self).finish()
        # we're done - record result
        for child in children:
            continue
        self.status = JobStatus.FINISHED
