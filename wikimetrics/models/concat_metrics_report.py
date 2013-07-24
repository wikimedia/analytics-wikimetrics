from wikimetrics.configurables import queue
import report
import pprint
from metric_report import MetricReport

__all__ = [
    'ConcatMetricsReport',
]


class ConcatMetricsReport(report.ReportNode):
    """
    Report which runs several metrics on the same cohort and then
    joins together the results from each metric into a suitable
    2-D representation.
    """
    
    def __init__(self, cohort, metrics):
        super(ConcatMetricsReport, self).__init__()
        self.cohort = cohort
        self.metrics = metrics
        # TODO enforce children always have a run @queue.task
        self.children = [MetricReport(cohort, metric) for metric in metrics]
        # TODO self.save()
    
    def finish(query_results):
        # we're done - record result
        for result in query_results:
            pprint.pprint(result)
    
    def __repr__(self):
        return '<ConcatMetricsReport("{0}")>'.format(self.persistent_id)
