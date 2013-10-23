from datetime import datetime, timedelta
from time import time
from nose.tools import assert_equal

from tests.fixtures import DatabaseTest, i
from wikimetrics.utils import format_date, CENSORED
from wikimetrics.metrics import Threshold
from wikimetrics.models import (
    Cohort, MetricReport, WikiUser, CohortWikiUser, MediawikiUser,
    Revision,
)


class ThresholdTest(DatabaseTest):
    
    def setUp(self):
        one_hour = timedelta(hours=1)
        reg = datetime.now() - one_hour * 48
        
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=2,
            revisions_per_editor=2,
            user_registrations=i(reg),
            revision_timestamps=[
                [i(reg + one_hour)     , i(reg + one_hour * 25)],
                [i(reg + one_hour * 30), i(reg + one_hour * 40)],
            ],
            revision_lengths=10
        )
    
    def test_case1_24h_count1(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
        )
        results = m(list(self.cohort), self.mwSession)
        
        assert_equal(results[self.editors[0].user_id][Threshold.id], True)
        assert_equal(results[self.editors[1].user_id][Threshold.id], False)
        assert_equal(results[self.editors[0].user_id][CENSORED], False)
        assert_equal(results[self.editors[1].user_id][CENSORED], False)
    
    def test_case1_72h_count1(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
            threshold_hours=3 * 24,
        )
        results = m(list(self.cohort), self.mwSession)
        
        assert_equal(results[self.editors[0].user_id][Threshold.id], True)
        assert_equal(results[self.editors[1].user_id][Threshold.id], True)
        assert_equal(results[self.editors[0].user_id][CENSORED], False)
        assert_equal(results[self.editors[1].user_id][CENSORED], False)
    
    def test_case1_72h_count3(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
            threshold_hours=3 * 24,
            number_of_edits=3,
        )
        results = m(list(self.cohort), self.mwSession)
        
        assert_equal(results[self.editors[0].user_id][Threshold.id], False)
        assert_equal(results[self.editors[1].user_id][Threshold.id], False)
        assert_equal(results[self.editors[0].user_id][CENSORED], True)
        assert_equal(results[self.editors[1].user_id][CENSORED], True)
    
    def test_case1_24h_count3(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
            threshold_hours=1 * 24,
            number_of_edits=3,
        )
        results = m(list(self.cohort), self.mwSession)
        
        assert_equal(results[self.editors[0].user_id][Threshold.id], False)
        assert_equal(results[self.editors[1].user_id][Threshold.id], False)
        assert_equal(results[self.editors[0].user_id][CENSORED], False)
        assert_equal(results[self.editors[1].user_id][CENSORED], False)

    def test_time_to_thershold(self):
        m = Threshold(
            namespaces=[self.survivors_namespace],
            threshold_hours=1 * 25,
            number_of_edits=2,
        )
        results = m(list(self.cohort), self.mwSession)

        assert_equal(results[self.editors[0].user_id][Threshold.time_to_threshold_id], 25)
        assert_equal(results[self.editors[1].user_id][Threshold.time_to_threshold_id], None)


