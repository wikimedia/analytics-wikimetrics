from nose.tools import assert_equal, assert_true
from tests.fixtures import WebTest


class TestHomeController(WebTest):
    
    def test_index(self):
        response = self.app.get('/')
        assert_equal(response.status_code, 200)
    
    def test_about(self):
        response = self.app.get('/about')
        assert_equal(response.status_code, 200)
    
    def test_favicon(self):
        response = self.app.get('/favicon.ico')
        assert_equal(response.status_code, 200)
    
    def test_support(self):
        response = self.app.get('/support')
        assert_equal(
            response.status_code, 200,
            '/ should get the support page'
        )
        
        assert_true(response.data.find('Mailing list') >= 0)
