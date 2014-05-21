from datetime import datetime, timedelta
from time import time
from nose.tools import assert_equal

from tests.fixtures import DatabaseTest, i, tz_note
from wikimetrics.utils import format_date, CENSORED
from wikimetrics.metrics import Threshold


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
        self.helper_insert_editors(
            editor_count=2,
            revisions_per_editor=2,
            user_registrations=i(reg),
            revision_timestamps=[
                [i(reg + one_hour)     , i(reg + one_hour * 25)],
                [i(reg + one_hour * 30), i(reg + one_hour * 40)],
            ],
            revision_lengths=10
        )
        
        self.e1 = self.editors[0].user_id
        self.e2 = self.editors[1].user_id
    
    def test_filters_out_other_editors(self):
        metric = Threshold(
            namespaces=[0],
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(len(results), 2)

    def test_runs_for_an_entire_wiki(self):
        metric = Threshold(
            namespaces=[0],
        )
        results = metric(None, self.mwSession)

        assert_equal(len(results), 4)
        assert_equal(results[self.e1][Threshold.id], True, tz_note)
        assert_equal(results[self.e2][Threshold.id], False, tz_note)
        assert_equal(results[self.e1][Threshold.time_to_threshold_id], 1, tz_note)
        assert_equal(results[self.e2][Threshold.time_to_threshold_id], None, tz_note)
        assert_equal(results[self.e1][CENSORED], False, tz_note)
        assert_equal(results[self.e2][CENSORED], False, tz_note)
        # NOTE: this is a bit precarious as it assumes the order of test data inserts
        assert_equal(results[self.e1 + 2][Threshold.id], True, tz_note)
        assert_equal(results[self.e1 + 2][Threshold.time_to_threshold_id], 1, tz_note)
        assert_equal(results[self.e1 + 2][CENSORED], False, tz_note)

    def test_case1_24h_count1(self):
        metric = Threshold(
            namespaces=[0],
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Threshold.id], True, tz_note)
        assert_equal(results[self.e2][Threshold.id], False, tz_note)
        assert_equal(results[self.e1][Threshold.time_to_threshold_id], 1, tz_note)
        assert_equal(results[self.e2][Threshold.time_to_threshold_id], None, tz_note)
        assert_equal(results[self.e1][CENSORED], False, tz_note)
        assert_equal(results[self.e2][CENSORED], False, tz_note)
    
    def test_case1_72h_count1(self):
        metric = Threshold(
            namespaces=[0],
            threshold_hours=72
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Threshold.id], True, tz_note)
        assert_equal(results[self.e2][Threshold.id], True, tz_note)
        assert_equal(results[self.e1][Threshold.time_to_threshold_id], 1, tz_note)
        assert_equal(results[self.e2][Threshold.time_to_threshold_id], 30, tz_note)
        assert_equal(results[self.e1][CENSORED], False, tz_note)
        assert_equal(results[self.e2][CENSORED], False, tz_note)
    
    def test_case1_72h_count3(self):
        metric = Threshold(
            namespaces=[0],
            threshold_hours=72,
            number_of_edits=3,
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Threshold.id], False, tz_note)
        assert_equal(results[self.e2][Threshold.id], False, tz_note)
        assert_equal(results[self.e1][Threshold.time_to_threshold_id], None, tz_note)
        assert_equal(results[self.e2][Threshold.time_to_threshold_id], None, tz_note)
        assert_equal(results[self.e1][CENSORED], True, tz_note)
        assert_equal(results[self.e2][CENSORED], True, tz_note)
    
    def test_case1_24h_count3(self):
        metric = Threshold(
            namespaces=[0],
            number_of_edits=3,
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Threshold.id], False, tz_note)
        assert_equal(results[self.e2][Threshold.id], False, tz_note)
        assert_equal(results[self.e1][Threshold.time_to_threshold_id], None, tz_note)
        assert_equal(results[self.e2][Threshold.time_to_threshold_id], None, tz_note)
        assert_equal(results[self.e1][CENSORED], False, tz_note)
        assert_equal(results[self.e2][CENSORED], False, tz_note)
    
    def test_time_to_thershold(self):
        metric = Threshold(
            namespaces=[0],
            threshold_hours=1 * 25,
            number_of_edits=2,
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Threshold.time_to_threshold_id], 25, tz_note)
        assert_equal(results[self.e2][Threshold.time_to_threshold_id], None, tz_note)
