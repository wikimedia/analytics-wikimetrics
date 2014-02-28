import json
import celery
import time
import unittest
import os.path
from nose.tools import assert_true, assert_equal, assert_false
from tests.fixtures import WebTest
from wikimetrics.models import PersistentReport
from wikimetrics.controllers.reports import (
    get_celery_task,
    get_celery_task_result,
    get_saved_report_path
)


def filterStatus(collection, status):
    return filter(lambda j : j['status'] == status, collection)


class ReportsControllerTest(WebTest):
    def setUp(self):
        WebTest.setUp(self)
        # add reports just for testing
        report_created = PersistentReport(
            user_id=self.owner_user_id,
            status=celery.states.PENDING,
            queue_result_key=None,
            show_in_ui=True
        )
        report_started = PersistentReport(
            user_id=self.owner_user_id,
            status=celery.states.STARTED,
            queue_result_key=None,
            show_in_ui=True
        )
        report_started2 = PersistentReport(
            user_id=self.owner_user_id,
            status=celery.states.STARTED,
            queue_result_key=None,
            show_in_ui=True
        )
        report_finished = PersistentReport(
            user_id=self.owner_user_id,
            status=celery.states.SUCCESS,
            queue_result_key=None,
            show_in_ui=True
        )
        self.session.add_all([
            report_created,
            report_started,
            report_started2,
            report_finished
        ])
        self.session.commit()
    
    def test_full_report_create_and_result(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-06-01 00:00:00',
                'end_date': '2013-09-01 00:00:00',
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
    
    def test_report_result_csv_error(self):
        response = self.app.get('/reports/result/blah.csv')
        assert_true(response.data.find('isError') >= 0)
    
    def test_report_result_json_error(self):
        response = self.app.get('/reports/result/blah.json')
        assert_true(response.data.find('isError') >= 0)
    
    def test_report_result_average_only_csv(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-05-01 00:00:00',
                'individualResults': False,
                'aggregateResults': True,
                'aggregateSum': False,
                'aggregateAverage': True,
                'aggregateStandardDeviation': False,
            },
        }]
        json_to_post = json.dumps(desired_responses)
        
        response = self.app.post('/reports/create/', data=dict(
            responses=json_to_post
        ))
        
        # Wait a second for the task to get processed
        time.sleep(1)
        
        # Check that the task has been created
        response = self.app.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        
        # Check the csv result
        response = self.app.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find('Average,,2.0') >= 0)

        # Testing to see if the parameters are also in the CSV
        # (related to Mingle 1089)
        assert_true(response.data.find('parameters') >= 0)
        assert_true(response.data.find('start_date') >= 0)
        assert_true(response.data.find('end_date') >= 0)
        assert_true(response.data.find('namespaces') >= 0)
        assert_true(response.data.find('metric/cohort') >= 0)
    
    def test_report_result_sum_only_csv(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-04-01 00:00:00',
                'individualResults': False,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        json_to_post = json.dumps(desired_responses)
        
        response = self.app.post('/reports/create/', data=dict(
            responses=json_to_post
        ))
        
        # Wait a second for the task to get processed
        time.sleep(1)
        
        # Check that the task has been created
        response = self.app.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        
        # Check the csv result
        response = self.app.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find('Sum,,8.0') >= 0)
    
    def test_report_result_std_dev_only_csv(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-04-01 00:00:00',
                'individualResults': False,
                'aggregateResults': True,
                'aggregateSum': False,
                'aggregateAverage': False,
                'aggregateStandardDeviation': True,
            },
        }]
        json_to_post = json.dumps(desired_responses)
        
        response = self.app.post('/reports/create/', data=dict(
            responses=json_to_post
        ))
        
        # Wait a second for the task to get processed
        time.sleep(1)
        
        # Check that the task has been created
        response = self.app.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        
        # Check the csv result
        response = self.app.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find('Standard Deviation') >= 0)

    def test_save_public_report(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'timeseries': 'month',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-05-01 00:00:00',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': False,
                'aggregateAverage': True,
                'aggregateStandardDeviation': False,
            },
        }]
        json_to_post = json.dumps(desired_responses)

        response = self.app.post('/reports/create/', data=dict(
            responses=json_to_post
        ))

        # Wait a second for the task to get processed
        time.sleep(1)

        # Check that the task has been created
        response = self.app.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)

        # Check if the file already exists on the local file system, and
        # remove it if necessary
        path = get_saved_report_path(report.id)
        if os.path.isfile(path):
            os.remove(path)

        # Make the report publically accessible (save it to static/public)
        response = self.app.post('/reports/save/{}'.format(report.id))
        assert_true(response.status_code == 200)

        # Check that the file exists on the local file system
        assert_true(os.path.isfile(path))

        # Now make the report private (remove it from static/public)
        response = self.app.post('/reports/remove/{}'.format(report.id))
        assert_true(response.status_code == 200)
        assert_false(os.path.isfile(path))

    def test_report_result_timeseries_csv(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'timeseries': 'month',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-05-01 00:00:00',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': False,
                'aggregateAverage': True,
                'aggregateStandardDeviation': False,
            },
        }]
        json_to_post = json.dumps(desired_responses)
        
        response = self.app.post('/reports/create/', data=dict(
            responses=json_to_post
        ))
        
        # Wait a second for the task to get processed
        time.sleep(1)
        
        # Check that the task has been created
        response = self.app.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        
        # Check the csv result
        response = self.app.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find(
            'user_id,user_name,submetric,'
            '2013-01-01 00:00:00,2013-02-01 00:00:00,'
            '2013-03-01 00:00:00,2013-04-01 00:00:00'
        ) >= 0)
        assert_true(response.data.find(
            '{0},{1},edits,1,2,1,0'.format(
                self.editors[0].user_id, self.editors[0].user_name)
        ) >= 0)
        assert_true(response.data.find(
            '{0},{1},edits,1,2,1,0'.format(
                self.editors[1].user_id, self.editors[1].user_name)
        ) >= 0)
        assert_true(response.data.find(
            'Average,,edits,0.5000,1.0000,0.5000,0.0000'
        ) >= 0)

        # Testing to see if the parameters are also in the CSV
        assert_true(response.data.find('parameters') >= 0)
        assert_true(response.data.find('start_date') >= 0)
        assert_true(response.data.find('end_date') >= 0)
        assert_true(response.data.find('namespaces') >= 0)
        assert_true(response.data.find('metric/cohort') >= 0)


class BasicTests(unittest.TestCase):
    
    def test_get_celery_task_no_key(self):
        (r1, r2) = get_celery_task(None)
        assert_equal(r1, None)
        assert_equal(r2, None)
    
    def test_get_celery_task_result_when_invalid(self):
        mock_task = MockTask(True)
        mock_report = MockReport()
        failure = get_celery_task_result(mock_task, mock_report)
        assert_true(failure['failure'], 'result not available')
    
    def test_get_celery_task_result_when_empty(self):
        mock_task = MockTask(False)
        mock_report = MockReport()
        failure = get_celery_task_result(mock_task, mock_report)
        assert_true(failure['failure'], 'result not available')


class MockTask(object):
    def __init__(self, invalid):
        self.invalid = invalid
        
    def get(self):
        if self.invalid:
            return 'invalid task result'
        else:
            return {}


class MockReport(object):
    def __init__(self):
        self.result_key = 'blah'
