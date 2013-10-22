from nose.tools import assert_equal
from wikimetrics.models import Cohort
from ..fixtures import DatabaseTest


class CohortTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_iter(self):
        self.editors[0].valid = False
        self.editors[1].valid = None
        self.session.commit()
        
        user_ids = list(self.cohort)
        assert_equal(self.editors[0].user_id in user_ids, False)
        assert_equal(self.editors[1].user_id in user_ids, False)
        assert_equal(self.editors[2].user_id in user_ids, True)
        assert_equal(self.editors[3].user_id in user_ids, True)
        assert_equal(len(user_ids), 2)
    
    def test_group_by_project(self):
        self.editors[0].valid = False
        self.editors[1].valid = None
        self.session.commit()
        
        grouped = self.cohort.group_by_project()
        user_ids = list(list(grouped)[0])
        assert_equal(self.editors[0].user_id in user_ids, False)
        assert_equal(self.editors[1].user_id in user_ids, False)
        assert_equal(self.editors[2].user_id in user_ids, True)
        assert_equal(self.editors[3].user_id in user_ids, True)
        assert_equal(len(user_ids), 2)
