from nose.tools import assert_true, assert_equal, nottest
from tests.fixtures import WebTest
import json
import celery
import logging

logger = logging.getLogger(__name__)


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
            len(filter(lambda j : j['status'] == celery.states.STARTED, parsed['reports'])),
            2,
            '/reports/list should return a list of report objects, '
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_list_pending(self):
        response = self.app.get('/reports/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filter(lambda j : j['status'] == celery.states.PENDING, parsed['reports'])),
            1,
            '/reports/list should return a list of report objects, '
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_list_success(self):
        response = self.app.get('/reports/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filter(lambda j : j['status'] == celery.states.SUCCESS, parsed['reports'])),
            1,
            '/reports/list should return a list of report objects,'
            'but instead returned:\n{0}'.format(response.data)
        )
    
    @nottest
    def test_create(self):
        post_data = []
        #post_data = {
            #"name":"Bytes Added - Algeria Summer Teahouse",
            #"cohort":{
                #"description":"",
                #"id":1,
                #"name":"Algeria Summer Teahouse",
                #"selected":True
            #},
            #"metric":{
                #"description":"Compute different aggregations of the bytes"\
                #        " contributed or removed from a  mediawiki project",
                #"label":"Bytes Added",
                #"name":"BytesAdded",
                #"id":"bytes-added",
                #"tabId":"metric-bytes-added",
                #"tabIdSelector":"#metric-bytes-added",
                #"selected":True,
                #"csrf_token":"20130709113638##91658fda06626f46b1f3bacf25e2038d824aef0e",
                #"start_date":"2012/1/1",
                #"end_date":"2013/1/1",
                #"namespaces":"0",
                #"positive_only_sum":True,
                #"negative_only_sum":True,
                #"absolute_sum":True,
                #"net_sum":True},
            #"tabId":"response-to-bytes-added-for-1",
            #"tabIdSelector":"#response-to-bytes-added-for-1"
        #}
        
        response = self.app.post('/reports/create/', data=post_data)
        logger.debug(response)
