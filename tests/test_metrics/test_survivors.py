from datetime import datetime
from time import time
from nose.tools import assert_equal

from tests.fixtures import DatabaseWithSurvivorCohortTest
from wikimetrics.metrics import Survivors
from wikimetrics.models import (
    Cohort, MetricReport, WikiUser, CohortWikiUser, MediawikiUser, 
    Revision
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

    def test_censored2(self):
        
        # NOTE: setting sunset_in_hours 10000 days in the future
        # This means that in 82 years, this test will break
        andrew_user = self.mwSession.query(MediawikiUser).filter(MediawikiUser.user_id == self.mw_andrew_id).first()
        andrew_revs = self.mwSession.query(Revision).join(MediawikiUser) \
                .filter(MediawikiUser.user_id==self.mw_andrew_id) \
                .order_by(Revision.rev_timestamp) \
                .all()

        m = Survivors(
            namespaces=[self.survivors_namespace],
            number_of_edits=2,
            survival_hours=int(((andrew_revs[2].rev_timestamp - andrew_user.user_registration).total_seconds())/(3600)),
            sunset_in_hours=2*48
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results, {
            self.mw_dan_id: {'censored': 0, 'survivor': 0},
            self.mw_evan_id: {'censored': 0, 'survivor': 0},
            self.mw_andrew_id: {'censored': 0, 'survivor': 1},
            self.mw_diederik_id: {'censored': 0, 'survivor': 0},
        })
