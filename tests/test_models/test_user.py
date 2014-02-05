from nose.tools import assert_equal
from wikimetrics.models import User
from ..fixtures import DatabaseTest


class UserTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_logout(self):
        user = self.session.query(User).get(self.owner_user_id)
        user.logout(self.session)
        user = self.session.query(User).get(self.owner_user_id)
        assert_equal(user.authenticated, False)
        assert_equal(user.active, False)
    
    def test_detach_from(self):
        user = self.session.query(User).get(self.owner_user_id)
        user.authenticated = False
        self.session.commit()
        
        user.detach_from(self.session)
        user.authenticated = True
        self.session.commit()
        
        user = self.session.query(User).get(self.owner_user_id)
        assert_equal(user.authenticated, False)
    
    def test_is_anonymous(self):
        user = self.session.query(User).get(self.owner_user_id)
        user.authenticated = False
        self.session.commit()
        assert_equal(user.is_anonymous(), True)
