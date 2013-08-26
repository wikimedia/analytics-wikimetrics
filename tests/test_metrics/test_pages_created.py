from nose.tools import assert_true, assert_not_equal, assert_equal
from tests.fixtures import DatabaseWithCohortTest

from wikimetrics import app
from wikimetrics.metrics import PagesCreated
from wikimetrics.models import Cohort, MetricReport, WikiUser, CohortWikiUser


class PagesCreatedTest(DatabaseWithCohortTest):
    # Evan has 3 pages created, one in namespace 301, one in 302, and one in 303
    # (see tests/fixtures.py for details)
    # So here we just test if the number of pages created in those namespaces is
    # actually 3
    def test_case_basic(self):
        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-20',
            end_date='2013-08-21'
        )
        results = metric(list(self.cohort), self.mwSession)
        assert_equal(results[self.evan_id]["pages_created"], 3)

    # same thing as before, but this time we leave one page created
    # out of the date range to see if date ranges work properly
    def test_case_uses_date_range(self):
        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-20',
            end_date='2013-07-21'
        )
        results = metric(list(self.cohort), self.mwSession)
        assert_equal(results[self.evan_id]["pages_created"], 2)
