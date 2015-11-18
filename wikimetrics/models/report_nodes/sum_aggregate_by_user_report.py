from collections import defaultdict
from report import ReportNode
from multi_project_metric_report import MultiProjectMetricReport
from wikimetrics.models.storage.wikiuser import WikiUserKey
from wikimetrics.api import CohortService
from wikimetrics.configurables import db
from wikimetrics.enums import Aggregation


__all__ = ['SumAggregateByUserReport']


class SumAggregateByUserReport(ReportNode):
    """
    A node responsible for aggregating the results of MultiProjectMetricReport
    by user, and formatting them as expected by RunGlobalReport. It specifically
    knows how to aggregate rolling active editor and newly registered metrics.
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
        super(SumAggregateByUserReport, self).__init__(*args, **kwargs)

        # Get mediawiki's username map to be able to aggregate.
        service = CohortService()
        session = db.get_session()
        self.usernames = service.get_wikiusernames_for_cohort(cohort.id, session)

        self.children = [
            MultiProjectMetricReport(cohort, metric, *args, **kwargs)
        ]

    def finish(self, child_results):
        results = child_results[0]  # One child only.

        # The way of aggregating results accross different projects
        # is applying the OR operator. Read more in the Wikitech docs:
        # https://wikitech.wikimedia.org/wiki/Analytics/Wikimetrics/Global_metrics
        aggregated_results = defaultdict(lambda: defaultdict(lambda: 0))
        for key_str, result in results.iteritems():
            key = WikiUserKey.fromstr(key_str)
            username = self.usernames[key]
            for metric_name in result:
                aggregated_results[username][metric_name] |= result[metric_name]

        # Finally, count all users that have a positive result.
        summed_results = defaultdict(lambda: 0)
        for mw_username, results in aggregated_results.iteritems():
            for metric_name, value in results.iteritems():
                summed_results[metric_name] += value

        # Encapsulate the results to be consistent with other metrics.
        return {Aggregation.SUM: summed_results}
