import json
import celery
import time
from nose.tools import assert_true, assert_equal
from tests.fixtures import WebTest
from wikimetrics.models import PersistentReport
from wikimetrics.controllers.reports import (
    get_celery_task,
    get_celery_task_result
)


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
        response = self.app.get('/reports/list/')
        parsed = json.loads(response.data)
        assert_equal(
            len(filterStatus(parsed['reports'], celery.states.SUCCESS)),
            1,
            '/reports/list should return a list of report objects,'
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_report_request_get(self):
        response = self.app.get('/reports/create/')
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('Create Analysis Report') >= 0)
    
    def test_full_report_create_and_result(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.test_cohort_id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-06-01',
                'end_date': '2013-09-01',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': True,
                'aggregateStandardDeviation': True,
            },
        }]
        json_to_post = json.dumps(desired_responses)
        
        response = self.app.post('/reports/create/', data=dict(
            responses=json_to_post
        ))
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/reports/') >= 0)
        
        # Wait a second for the task to get processed
        time.sleep(1)
        
        # Check that the task has been created
        response = self.app.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        assert_true(task is not None)
        
        # Get the result directly
        result = get_celery_task_result(task, report)
        assert_true(result is not None)
        
        # Check the status via get
        response = self.app.get('/reports/status/{0}'.format(result_key))
        assert_true(response.data.find('SUCCESS') >= 0)
        
        # Check the csv result
        response = self.app.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find('Average') >= 0)
        
        # Check the json result
        response = self.app.get('/reports/result/{0}.json'.format(result_key))
        assert_true(response.data.find('Average') >= 0)
        
        # Purposefully change the report status to make sure update_status works
        report.status = celery.states.STARTED
        self.session.add(report)
        self.session.commit()
        report_new = self.session.query(PersistentReport).get(report.id)
        self.session.expunge(report_new)
        report_new.update_status()
        assert_equal(report_new.status, celery.states.SUCCESS)
    
    def test_report_result_csv_error(self):
        response = self.app.get('/reports/result/blah.csv')
        assert_true(response.data.find('isError') >= 0)
    
    def test_report_result_json_error(self):
        response = self.app.get('/reports/result/blah.json')
        assert_true(response.data.find('isError') >= 0)
