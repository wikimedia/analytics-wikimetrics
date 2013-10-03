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


class ReportsControllerTest(WebTest):
    
    def setUp(self):
        WebTest.setUp(self)
        self.create_test_cohort(
            editor_count=2,
            revisions_per_editor=4,
            revision_timestamps=[
                [20130101000001, 20130201010000, 20130201010100, 20130301020100],
                [20130101000001, 20130201010000, 20130201010100, 20130301020100]
            ],
            revision_lengths=10,
            owner_user_id=self.test_web_user_id,
        )
    
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
        assert_true(response.data.find('Average,4.0') >= 0)

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
        assert_true(response.data.find('Sum,8.0') >= 0)
    
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
            'user_id,submetric,'
            '2013-01-01 00:00:00,2013-02-01 00:00:00,'
            '2013-03-01 00:00:00,2013-04-01 00:00:00'
        ) >= 0)
        assert_true(response.data.find(
            '{0},edits,1,2,1,0'.format(self.editors[0].user_id)
        ) >= 0)
        assert_true(response.data.find(
            '{0},edits,1,2,1,0'.format(self.editors[1].user_id)
        ) >= 0)
        assert_true(response.data.find(
            'Average,edits,1.0,2.0,1.0,0.0'
        ) >= 0)

        # Testing to see if the parameters are also in the CSV
        assert_true(response.data.find('parameters') >= 0)
        assert_true(response.data.find('start_date') >= 0)
        assert_true(response.data.find('end_date') >= 0)
        assert_true(response.data.find('namespaces') >= 0)
        assert_true(response.data.find('metric/cohort') >= 0)
