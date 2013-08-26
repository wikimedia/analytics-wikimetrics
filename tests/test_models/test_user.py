from nose.tools import assert_equals, assert_true, raises
from wikimetrics.models import User
from ..fixtures import DatabaseTest


class UserTest(DatabaseTest):
    
    def test_logout(self):
        user = self.session.query(User).get(self.test_web_user_id)
        user.logout(self.session)
        user = self.session.query(User).get(self.test_web_user_id)
        assert_equals(user.authenticated, False)
        assert_equals(user.active, False)
    
    def test_detach_from(self):
        user = self.session.query(User).get(self.test_web_user_id)
        user.authenticated = False
        self.session.commit()
        
        user.detach_from(self.session)
        user.authenticated = True
        self.session.commit()
        
        user = self.session.query(User).get(self.test_web_user_id)
        assert_equals(user.authenticated, False)
    
    def test_is_anonymous(self):
        user = self.session.query(User).get(self.test_web_user_id)
        user.authenticated = False
        self.session.commit()
        
        assert_equals(user.is_anonymous(), True)
