from nose.tools import assert_true, assert_not_equal, assert_equal
from tests.fixtures import DatabaseWithCohortTest

from wikimetrics import app
from wikimetrics.metrics import PagesCreated
from wikimetrics.models import Cohort, MetricReport, WikiUser, CohortWikiUser


class PagesCreatedTest(DatabaseWithCohortTest):
    # TODO: add tests
    def test_case1(self):
        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-01',
            end_date='2013-08-01'
        )
        results = metric(list(self.cohort), self.mwSession)
        assert_equal(results[self.evan_id]["pages_created"], 3)
