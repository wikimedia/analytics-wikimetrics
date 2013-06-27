from nose.tools import assert_true, assert_equal
from tests.fixtures import WebTest
import json
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class TestJobsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/jobs/', follow_redirects=True)
        assert_true(
            response._status_code == 200,
            '/jobs should get the list of jobs for the current user'
        )
    
    def test_list_started(self):
        response = self.app.get('/jobs/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filter(lambda j : j['status'] == 'STARTED', parsed['jobs'])),
            2,
            '/jobs/list should return a list of job objects, '
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_list_created(self):
        response = self.app.get('/jobs/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filter(lambda j : j['status'] == 'CREATED', parsed['jobs'])),
            1,
            '/jobs/list should return a list of job objects, '
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_list_finished(self):
        response = self.app.get('/jobs/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filter(lambda j : j['status'] == 'FINISHED', parsed['jobs'])),
            1,
            '/jobs/list should return a list of job objects,'
            'but instead returned:\n{0}'.format(response.data)
        )
