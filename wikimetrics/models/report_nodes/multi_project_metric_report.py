from celery.utils.log import get_task_logger
from wikimetrics.api import CohortService
from report import ReportNode
from metric_report import MetricReport


__all__ = ['MultiProjectMetricReport']

task_logger = get_task_logger(__name__)


class MultiProjectMetricReport(ReportNode):
    """
    A node responsbile for running a single metric on a potentially
    project-heterogenous cohort. This just abstracts away the task
    of grouping the cohort by project and calling a MetricReport on
    each project-homogenous list of user_ids.
    """
    show_in_ui = False
    
    def __init__(self, cohort, metric, *args, **kwargs):
        """
        Parameters:
            metric  : an instance of a Metric class
            cohort  : a logical cohort object
            args    : should include any parameters needed by ReportNode
            kwargs  : should include any parameters needed by ReportNode
        """
        super(MultiProjectMetricReport, self).__init__(*args, **kwargs)
        
        cohort_service = CohortService()
        self.children = []
        for project, user_ids in cohort_service.get_users_by_project(cohort):
            # note that user_ids is actually just an iterator
            self.children.append(
                MetricReport(metric, cohort.id, user_ids, project, *args, **kwargs)
            )
    
    def finish(self, metric_results):
        merged_individual_results = {}
        for res in metric_results:
            merged_individual_results.update(res)
        
        return merged_individual_results
    
    def __repr__(self):
        return '<MultiProjectMetricReport("{0}")>'.format(self.persistent_id)
