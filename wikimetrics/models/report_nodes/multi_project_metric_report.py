import json
from wikimetrics.configurables import queue
from celery.utils.log import get_task_logger
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
        super(MultiProjectMetricReport, self).__init__(
            *args,
            **kwargs
        )
        self.cohort = cohort
        self.metric = metric
        
        self.children = []
        for project, user_ids in cohort.group_by_project():
            # note that user_ids is actually just an iterator
            self.children.append(MetricReport(metric, user_ids, project))
    
    def finish(self, metric_results):
        merged_individual_results = {}
        # TODO: handle collisions where the same ID is used accross projects
        for res in metric_results:
            merged_individual_results.update(res)
        
        result = self.report_result(merged_individual_results)
        return result
    
    def __repr__(self):
        return '<MultiProjectMetricReport("{0}")>'.format(self.persistent_id)
