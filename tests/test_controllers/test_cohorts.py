import pprint
from nose.tools import *
from tests.fixtures import *


class TestCohortsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/cohorts/')
        assert_true(
            response._status_code == 200,
            '/cohorts should get the list of cohorts'
        )
