from nose.tools import assert_true, \
    assert_not_equal, assert_equal, assert_in, assert_not_in
from tests.fixtures import DatabaseWithSurvivorCohortTest

from wikimetrics import app
from wikimetrics.metrics import Survivors
from wikimetrics.models import Cohort, MetricReport, WikiUser, CohortWikiUser
from pprint import pprint
import sys


class SurvivorsTest(DatabaseWithSurvivorCohortTest):

    def test_convert_dates_to_timestamps(self):
        m = Survivors(
            namespaces=[304],
            start_date=1375660800
        )

        try:
            m.convert_dates_to_timestamps()
        except Exception as e:
            assert_equal(1, 1, "Exception thrown")
            assert_equal(str(e), "Problems with start_date")

        m = Survivors(
            namespaces=[304],
            end_date=1375660800
        )

        try:
            m.convert_dates_to_timestamps()
        except Exception as e:
            assert_equal(str(e), "Problems with end_date")

    # registration YES ; survival_days YES ;
    def test_case_RS(self):
        m = Survivors(
            namespaces=[304],
            survival_days=4,
            use_registration_date=True,
        )
        results = m(list(self.cohort), self.mwSession)

        #pprint(results,sys.stderr)
        assert_equal(results[self.dan_id]["survivors"], False)
        assert_equal(results[self.evan_id]["survivors"], False)
        assert_equal(results[self.andrew_id]["survivors"], True)

    # registration NO ; survival_days YES ;
    def test_case_rS(self):
        m = Survivors(
            namespaces=[304],
            start_date='2013-01-03',
            survival_days='2'
        )
        results = m(list(self.cohort), self.mwSession)

        pprint(results, sys.stderr)
        assert_equal(results[self.dan_id]["survivors"], False)
        assert_equal(results[self.evan_id]["survivors"], True)
        assert_equal(results[self.andrew_id]["survivors"], True)

    # registration YES ; survival_days NO ;
    def test_case_Rs(self):
        m = Survivors(
            namespaces=[304],
            use_registration_date=True,
            end_date='2013-01-06',
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.dan_id]["survivors"], False)
        assert_equal(results[self.evan_id]["survivors"], False)
        assert_equal(results[self.andrew_id]["survivors"], True)

    # registration NO  ; survival_days NO ;
    def test_case_rs(self):
        m = Survivors(
            namespaces=[304],
            start_date='2013-01-01',
            end_date='2013-01-04',
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.dan_id]["survivors"], False)
        assert_equal(results[self.evan_id]["survivors"], True)
        assert_equal(results[self.andrew_id]["survivors"], True)
