from wikimetrics.configurables import queue
import job
import pprint
from metric_job import MetricJob

__all__ = [
    'ConcatMetricsJob',
]


class ConcatMetricsJob(job.JobNode):
    """
    Job which runs several metrics on the same cohort and then
    joins together the results from each metric into a suitable
    2-D representation.
    """
    
    def __init__(self, cohort, metrics):
        super(ConcatMetricsJob, self).__init__()
        self.cohort = cohort
        self.metrics = metrics
        # TODO enforce children always have a run @queue.task
        self.children = [MetricJob(cohort, metric) for metric in metrics]
        # TODO self.save()
    
    @queue.task
    def finish(query_results):
        # we're done - record result
        for result in query_results:
            pprint.pprint(result)
