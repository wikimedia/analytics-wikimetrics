from wikimetrics.configurables import queue
import report
from .multi_project_metric_report import MultiProjectMetricReport

__all__ = [
    'RunReport',
]


class RunReport(report.ReportNode):
    """
    Represents a batch of cohort-metric reports created by the
    user during a single reports/create/ workflow.  This is also
    intended to be the unit of work which could be easily re-run.
    """
    
    show_in_ui = False
    
    def __init__(self, cohort_metrics_reports, *args, **kwargs):
        """
        Parameters:
        
            cohort_metrics [(Cohort, Metric),...]  : list of cohort-metric pairs to be run
        """
        super(RunReport, self).__init__(*args, **kwargs)
        self.children = cohort_metrics_reports
    
    def finish(self, report_results):
        return report_results
    
    def __repr__(self):
        return '<RunReport("{0}")>'.format(self.persistent_id)
