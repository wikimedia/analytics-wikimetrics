from nose.tools import assert_true, assert_equal, nottest
from tests.fixtures import WebTest
import json
import celery


def filterStatus(collection, status):
    return filter(lambda j : j['status'] == status, collection)


class TestReportsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/reports/', follow_redirects=True)
        assert_true(
            response._status_code == 200,
            '/reports should get the list of reports for the current user'
        )
    
    def test_list_started(self):
        response = self.app.get('/reports/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filterStatus(parsed['reports'], celery.states.STARTED)),
            2,
            '/reports/list should return a list of report objects, '
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_list_pending(self):
        response = self.app.get('/reports/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filterStatus(parsed['reports'], celery.states.PENDING)),
            1,
            '/reports/list should return a list of report objects, '
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_list_success(self):
        response = self.app.get('/reports/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filterStatus(parsed['reports'], celery.states.SUCCESS)),
            1,
            '/reports/list should return a list of report objects,'
            'but instead returned:\n{0}'.format(response.data)
        )
