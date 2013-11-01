from nose.tools import assert_equal, assert_true, raises
from tests.fixtures import WebTestAnonymous, WebTest
from flask.ext.login import current_user
from flask_oauth import OAuthException


class TestAuthenticationControllerLoggedOut(WebTestAnonymous):
    
    def test_login_redirect(self):
        response = self.app.get('/metrics', follow_redirects=True)
        assert_equal(
            response.status_code, 200,
            '/metrics should redirect to a login page'
        )
        assert_true(
            response.data.find('Please Login before visiting') >= 0,
            'The default_to_private method should be invoked'
        )
    
    def test_login_required_via_ajax(self):
        response = self.app.get('/metrics', follow_redirects=True, headers=[
            ('X-Requested-With', 'XMLHttpRequest')
        ])
        assert_equal(response.status_code, 200)
        assert_true(
            response.data.find('isError') >= 0,
            'Can''t access private routes via ajax'
        )
    
    @raises(RuntimeError)
    # NOTE: does not cover line 82 as expected
    def test_logout(self):
        
        self.app.get('/login-for-testing-only')
        assert_true(current_user.is_authenticated)
        self.app.get('/logout')
        
        # This will throw an exception because the current user is logged out
        print(current_user.is_authenticated)
    
    def test_login_google(self):
        response = self.app.get('/login/google')
        assert_true(
            response.data.find('accounts.google') >= 0,
            'should redirect to google'
        )
        assert_equal(
            response.status_code,
            302
        )
    
    @raises(OAuthException)
    # NOTE: does not cover lines 108 - 150 as expected
    def test_auth_google(self):
        self.app.get('/auth/google?code=hello')
    # NOTE: can't figure out how to cover 155
    
    def test_login_twitter(self):
        response = self.app.get('/login/twitter')
        assert_equal(response.data, 'Not Implemented Yet')
    
    def test_auth_twitter(self):
        response = self.app.get('/auth/twitter')
        assert_equal(response.data, 'Not Implemented Yet')


class TestAuthenticationControllerLoggedIn(WebTest):
    
    def test_no_redirect_when_logged_in(self):
        response = self.app.get('/metrics', follow_redirects=True)
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('<h2>Metrics</h2>') >= 0)
