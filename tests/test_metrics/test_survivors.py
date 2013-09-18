from nose.tools import assert_true, \
    assert_not_equal, assert_equal, assert_in, assert_not_in
from tests.fixtures import DatabaseWithSurvivorCohortTest

from wikimetrics import app
from wikimetrics.metrics import Survivors
from wikimetrics.models import Cohort, MetricReport, WikiUser, CohortWikiUser
from pprint import pprint
from datetime import datetime
import sys


class SurvivorsTest(DatabaseWithSurvivorCohortTest):

    def test_case1_24h_count1(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
            survival_hours=1 * 24
        )
        results = m(list(self.cohort), self.mwSession)

        pprint(results, sys.stderr)
        assert_equal(results[self.mw_dan_id]["survivors"], True)
        assert_equal(results[self.mw_evan_id]["survivors"], True)
        assert_equal(results[self.mw_andrew_id]["survivors"] , True)

    def test_case1_72h_count1(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
            survival_hours=3 * 24
        )
        results = m(list(self.cohort), self.mwSession)

        pprint(results, sys.stderr)
        assert_equal(results[self.mw_dan_id]["survivors"], False)
        assert_equal(results[self.mw_evan_id]["survivors"], False)
        assert_equal(results[self.mw_andrew_id]["survivors"] , True)

    def test_case1_24h_count3(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
            survival_hours=1 * 24,
            number_of_edits=3
        )
        results = m(list(self.cohort), self.mwSession)

        pprint(results, sys.stderr)
        assert_equal(results[self.mw_dan_id]["survivors"], False)
        assert_equal(results[self.mw_evan_id]["survivors"], False)
        assert_equal(results[self.mw_andrew_id]["survivors"] , True)

    def test_case2_24h_count3_sunset72h(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
            survival_hours=1 * 24,
            number_of_edits=3,
            sunset=3 * 24
        )
        results = m(list(self.cohort), self.mwSession)

        pprint(results, sys.stderr)
        assert_equal(results[self.mw_dan_id]["survivors"], False)
        assert_equal(results[self.mw_evan_id]["survivors"], False)
        assert_equal(results[self.mw_andrew_id]["survivors"] , True)

    def test_edgecase(self):
        m = Survivors(
            namespaces=[self.survivors_namespace],
        )
        results = m(list(self.cohort), self.mwSession)

        pprint(results, sys.stderr)
        assert_equal(results[self.mw_dan_id]["survivors"], True)
        assert_equal(results[self.mw_evan_id]["survivors"], True)
        assert_equal(results[self.mw_andrew_id]["survivors"] , True)
