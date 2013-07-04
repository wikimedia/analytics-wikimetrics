import pprint
import json
from nose.tools import assert_equal
from tests.fixtures import WebTest


class TestCohortsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/cohorts/', follow_redirects=True)
        assert_equal(
            response.status_code, 200,
            '/cohorts should get the list of cohorts'
        )
    
    def test_list(self):
        response = self.app.get('/cohorts/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filter(lambda c : c['name'] == 'test_private', parsed['cohorts'])),
            1,
            '/cohorts/list should include a cohort named test_private, '
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_detail(self):
        response = self.app.get('/cohorts/detail/1', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(parsed['wikiusers']),
            4,
            '/cohorts/detail/1 should return JSON object with key `wikiusers`'
            'for a list of length 4== `test`, but instead returned: {0}'.format(parsed)
        )
