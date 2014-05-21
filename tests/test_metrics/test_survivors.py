from datetime import datetime, timedelta
from time import time
from nose.tools import assert_equal

from tests.fixtures import DatabaseTest, i
from wikimetrics.metrics import Survival


class SurvivalTest(DatabaseTest):
    
    def setUp(self):
        one_hour = timedelta(hours=1)
        reg = datetime.now() - one_hour * 48
        
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=3,
            revisions_per_editor=2,
            user_registrations=i(reg),
            revision_timestamps=[
                [i(reg + one_hour)     , i(reg + one_hour * 25)],
                [i(reg + one_hour * 20), i(reg + one_hour * 40)],
                [i(reg + one_hour * 30), i(reg + one_hour * 73)],
            ],
            revision_lengths=10
        )
        self.helper_insert_editors(
            editor_count=3,
            revisions_per_editor=2,
            user_registrations=i(reg),
            revision_timestamps=[
                [i(reg + one_hour)     , i(reg + one_hour * 25)],
                [i(reg + one_hour * 20), i(reg + one_hour * 40)],
                [i(reg + one_hour * 30), i(reg + one_hour * 73)],
            ],
            revision_lengths=10
        )
        
        self.e1 = self.editors[0].user_id
        self.e2 = self.editors[1].user_id
        self.e3 = self.editors[2].user_id
    
    def test_filters_out_other_editors(self):
        metric = Survival(
            namespaces=[0],
            survival_hours=24,
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(len(results), 3)

    def test_runs_for_an_entire_wiki(self):
        metric = Survival(
            namespaces=[0],
            survival_hours=24,
        )
        results = metric(None, self.mwSession)

        assert_equal(len(results), 6)
        assert_equal(results[self.e1][Survival.id], True)
        assert_equal(results[self.e2][Survival.id], True)
        assert_equal(results[self.e3][Survival.id] , True)
        # NOTE: this is a bit precarious as it assumes the order of test data inserts
        assert_equal(results[self.e1 + 3][Survival.id], True)

    def test_case1_24h_count1(self):
        metric = Survival(
            namespaces=[0],
            survival_hours=24,
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Survival.id], True)
        assert_equal(results[self.e2][Survival.id], True)
        assert_equal(results[self.e3][Survival.id] , True)
    
    def test_case1_72h_count1(self):
        metric = Survival(
            namespaces=[0],
            survival_hours=72,
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Survival.id], False)
        assert_equal(results[self.e2][Survival.id], False)
        assert_equal(results[self.e3][Survival.id] , True)
    
    def test_case1_24h_count3(self):
        metric = Survival(
            namespaces=[0],
            survival_hours=1 * 24,
            number_of_edits=3,
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Survival.id], False)
        assert_equal(results[self.e2][Survival.id], False)
        assert_equal(results[self.e3][Survival.id], False)
    
    def test_case2_24h_count2_sunset72h(self):
        metric = Survival(
            namespaces=[0],
            survival_hours=24,
            number_of_edits=2,
            sunset_in_hours=72,
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results[self.e1][Survival.id], False)
        assert_equal(results[self.e2][Survival.id], False)
        assert_equal(results[self.e3][Survival.id] , True)
    
    def test_default(self):
        metric = Survival(
            namespaces=[0],
        )
        results = metric(self.editor_ids, self.mwSession)
        #self.debug_query = m.debug_query
        
        assert_equal(results[self.e1][Survival.id], True)
        assert_equal(results[self.e2][Survival.id], True)
        assert_equal(results[self.e3][Survival.id] , True)
    
    def test_censored1(self):
        metric = Survival(
            namespaces=[0],
            number_of_edits=3,
            survival_hours=24,
            sunset_in_hours=30000 * 24
        )
        results = metric(self.editor_ids, self.mwSession)
        assert_equal(results, {
            self.e1: {'censored': 1, Survival.id: 0},
            self.e2: {'censored': 1, Survival.id: 0},
            self.e3: {'censored': 1, Survival.id: 0},
        })
    
    def test_censored2(self):
        metric = Survival(
            namespaces=[0],
            number_of_edits=2,
            survival_hours=0,
            sunset_in_hours=26
        )
        results = metric(self.editor_ids, self.mwSession)
        
        assert_equal(results, {
            self.e1: {'censored': 0, Survival.id: 1},
            self.e2: {'censored': 0, Survival.id: 0},
            self.e3: {'censored': 0, Survival.id: 0},
        })
