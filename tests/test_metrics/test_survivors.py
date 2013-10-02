from datetime import datetime
from nose.tools import assert_equal

from tests.fixtures import DatabaseWithSurvivorCohortTest
from wikimetrics.metrics import Survivors
from wikimetrics.models import (
    Cohort, MetricReport, WikiUser, CohortWikiUser, MediawikiUser,
)


class SurvivorsTest(DatabaseWithSurvivorCohortTest):
    
    def test_case1_24h_count1(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
            survival_hours=1 * 24
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.mw_dan_id]["survivor"], True)
        assert_equal(results[self.mw_evan_id]["survivor"], True)
        assert_equal(results[self.mw_andrew_id]["survivor"] , True)
    
    def test_case1_72h_count1(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
            survival_hours=3 * 24
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.mw_dan_id]["survivor"], False)
        assert_equal(results[self.mw_evan_id]["survivor"], False)
        assert_equal(results[self.mw_andrew_id]["survivor"] , True)
    
    def test_case1_24h_count3(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
            survival_hours=1 * 24,
            number_of_edits=3
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.mw_dan_id]["survivor"], False)
        assert_equal(results[self.mw_evan_id]["survivor"], False)
        assert_equal(results[self.mw_andrew_id]["survivor"] , True)
    
    def test_case2_24h_count3_sunset72h(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
            survival_hours=1 * 24,
            number_of_edits=3,
            sunset_in_hours=3 * 24
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.mw_dan_id]["survivor"], False)
        assert_equal(results[self.mw_evan_id]["survivor"], False)
        assert_equal(results[self.mw_andrew_id]["survivor"] , True)
    
    def test_default(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
        )
        results = m(list(self.cohort), self.mwSession)
        #self.debug_query = m.debug_query

        assert_equal(results[self.mw_dan_id]["survivor"], True)
        assert_equal(results[self.mw_evan_id]["survivor"], True)
        assert_equal(results[self.mw_andrew_id]["survivor"] , True)
    
    # for [T+t,today] the observation is censored
    def test_censored1(self):
        
        # NOTE: setting sunset_in_hours 10000 days in the future
        # This means that in 82 years, this test will break
        m = Survivors(
            namespaces=[self.survivors_namespace],
            number_of_edits=6,
            survival_hours=30000 * 24,
            sunset_in_hours=30000 * 24
        )
        results = m(list(self.cohort), self.mwSession)
        assert_equal(results, {
            self.mw_dan_id: {'censored': 1, 'survivor': 0},
            self.mw_evan_id: {'censored': 1, 'survivor': 0},
            self.mw_andrew_id: {'censored': 1, 'survivor': 0},
            self.mw_diederik_id: {'censored': 0, 'survivor': 0},
        })
