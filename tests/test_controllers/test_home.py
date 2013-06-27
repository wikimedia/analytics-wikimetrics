from nose.tools import assert_equal
from tests.fixtures import WebTest


class TestHomeController(WebTest):
    
    def test_index(self):
        response = self.app.get('/', follow_redirects=True)
        assert_equal(
            response._status_code, 200,
            '/ should get the home page'
        )
