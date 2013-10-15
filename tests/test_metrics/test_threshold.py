from datetime import datetime
from time import time
from nose.tools import assert_equal

from tests.fixtures import DatabaseWithSurvivorCohortTest
from wikimetrics.metrics import Threshold
from wikimetrics.models import (
    Cohort, MetricReport, WikiUser, CohortWikiUser, MediawikiUser,
    Revision,
)


metric_name = Threshold.id


class ThresholdTest(DatabaseWithSurvivorCohortTest):
    
    def test_case1_24h_count1(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
            survival_hours=1 * 24
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.mw_dan_id][metric_name], True)
        assert_equal(results[self.mw_evan_id][metric_name], True)
        assert_equal(results[self.mw_andrew_id][metric_name] , True)
    
    def test_case1_72h_count1(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
            survival_hours=3 * 24
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.mw_dan_id][metric_name], False)
        assert_equal(results[self.mw_evan_id][metric_name], False)
        assert_equal(results[self.mw_andrew_id][metric_name] , True)
    
    def test_case1_24h_count3(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
            survival_hours=1 * 24,
            number_of_edits=3
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.mw_dan_id][metric_name], False)
        assert_equal(results[self.mw_evan_id][metric_name], False)
        assert_equal(results[self.mw_andrew_id][metric_name] , True)
    
    def test_default(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
        )
        results = m(list(self.cohort), self.mwSession)
        #self.debug_query = m.debug_query

        assert_equal(results[self.mw_dan_id][metric_name], True)
        assert_equal(results[self.mw_evan_id][metric_name], True)
        assert_equal(results[self.mw_andrew_id][metric_name] , True)
