from nose.tools import *
from tests.fixtures import *


class TestJobsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/jobs/', follow_redirects=True)
        assert_true(
            response._status_code == 200,
            '/jobs should get the list of jobs for the current user'
        )
