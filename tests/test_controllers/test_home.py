from nose.tools import *
from tests.fixtures import *


class TestHomeController(WebTest):
    
    def test_index(self):
        response = self.app.get('/')
        assert_true(
            response._status_code == 200,
            '/ should get the home page'
        )
