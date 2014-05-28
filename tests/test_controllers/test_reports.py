import json
import celery
import time
import unittest
import os.path
from mock import Mock, MagicMock
from contextlib import contextmanager
from flask import appcontext_pushed, g
from nose.tools import assert_true, assert_equal, assert_false, raises
from datetime import date, timedelta

from tests.fixtures import WebTest, mediawiki_project, second_mediawiki_project
from wikimetrics.models import (
    ReportStore, WikiUserStore, CohortStore, CohortWikiUserStore, MediawikiUser
)
from wikimetrics.api import PublicReportFileManager
from wikimetrics.exceptions import InvalidCohort
from wikimetrics.controllers.reports import (
    get_celery_task,
)
from wikimetrics.configurables import app, get_absolute_path, db, queue


@contextmanager
def file_manager_set(app, file_manager):
    def handler(sender, **kwargs):
        g.file_manager = file_manager
    with appcontext_pushed.connected_to(handler, app):
        yield


def filterStatus(collection, status):
    return filter(lambda j : j['status'] == status, collection)


class ControllerAsyncTest(WebTest):
    
    def setUp(self):
        # it is too bad but until we remove usage of AsyncResult in the codebase
        # there is no way to make these tests synchronous
        # thus overriding queue config so these tests
        # use celery in async mode
        queue.conf['CELERY_ALWAYS_EAGER'] = False
        WebTest.setUp(self)
    
    def tearDown(self):
        queue.conf['CELERY_ALWAYS_EAGER'] = True
        WebTest.tearDown(self)


class ReportsControllerTest(ControllerAsyncTest):
    
    def setUp(self):
        ControllerAsyncTest.setUp(self)
        # add reports just for testing
        report_created = ReportStore(
            user_id=self.owner_user_id,
            status=celery.states.PENDING,
            queue_result_key=None,
            show_in_ui=True
        )
        report_started = ReportStore(
            user_id=self.owner_user_id,
            status=celery.states.STARTED,
            queue_result_key=None,
            show_in_ui=True
        )
        report_started2 = ReportStore(
            user_id=self.owner_user_id,
            status=celery.states.STARTED,
            queue_result_key=None,
            show_in_ui=True
        )
        report_finished = ReportStore(
            user_id=self.owner_user_id,
            status=celery.states.SUCCESS,
            queue_result_key=None,
            show_in_ui=True
        )
        report_recurrent = ReportStore(
            user_id=self.owner_user_id,
            status=celery.states.SUCCESS,
            queue_result_key=None,
            show_in_ui=True,
            recurrent=True
        )
        self.past_date = date.today() - timedelta(days=60)
        
        report_recurrent_two_months_ago = ReportStore(
            user_id=self.owner_user_id,
            status=celery.states.SUCCESS,
            queue_result_key=None,
            show_in_ui=True,
            created=self.past_date,
            recurrent=True
        )
        self.session.add_all([
            report_created,
            report_started,
            report_started2,
            report_finished,
            report_recurrent,
            report_recurrent_two_months_ago,
        ])
        self.session.commit()
        
    def test_full_report_create_and_result(self):
        
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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

        response = self.client.post('/reports/create/', data=dict(
            responses=json_to_post
        ))
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/reports/') >= 0)

        # Wait a second for the task to get processed
        time.sleep(1)

        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        assert_true(task is not None)

        # Get the result directly
        result = task.get()
        assert_true(result is not None)
       
        # Check the status via get
        response = self.client.get('/reports/status/{0}'.format(result_key))
        assert_true(response.data.find('SUCCESS') >= 0)

        # Check the csv result
        response = self.client.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find('Average') >= 0)

        # Check the json result
        response = self.client.get('/reports/result/{0}.json'.format(result_key))
        assert_true(response.data.find('Average') >= 0)

    def test_index(self):
        response = self.client.get('/reports/', follow_redirects=True)
        assert_true(
            response._status_code == 200,
            '/reports should get the list of reports for the current user'
        )

    def test_list_started(self):
        response = self.client.get('/reports/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filterStatus(parsed['reports'], celery.states.STARTED)),
            2,
            '/reports/list should return a list of report objects, '
            'but instead returned:\n{0}'.format(response.data)
        )

    def test_list_pending(self):
        response = self.client.get('/reports/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filterStatus(parsed['reports'], celery.states.PENDING)),
            1,
            '/reports/list should return a list of report objects, '
            'but instead returned:\n{0}'.format(response.data)
        )

    def test_list_success(self):
        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        assert_equal(
            len(filterStatus(parsed['reports'], celery.states.SUCCESS)),
            3,
            '/reports/list should return a list of report objects,'
            'but instead returned:\n{0}'.format(response.data)
        )
        # data should display the report created a while back
        assert_true(str(self.past_date) in str(parsed))

    def test_report_request_get(self):
        response = self.client.get('/reports/create/')
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('Create Report') >= 0)

    def test_report_result_csv_error(self):
        response = self.client.get('/reports/result/blah.csv')
        assert_true(response.data.find('isError') >= 0)

    def test_report_result_json_error(self):
        response = self.client.get('/reports/result/blah.json')
        assert_true(response.data.find('isError') >= 0)

    def test_report_result_average_only_csv(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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

        response = self.client.post('/reports/create/', data=dict(
            responses=json_to_post
        ))

        # Wait a second for the task to get processed
        time.sleep(1)

        # Check that the task has been created
        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)

        # Check the csv result
        response = self.client.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find('Average,,,2.0') >= 0)

        # Testing to see if the parameters are also in the CSV
        # (related to Mingle 1089)
        assert_true(response.data.find('parameters') >= 0)
        assert_true(response.data.find('start_date') >= 0)
        assert_true(response.data.find('end_date') >= 0)
        assert_true(response.data.find('namespaces') >= 0)
        cohort_size = 'Cohort Size,{0}'.format(len(self.cohort))
        assert_true(response.data.find(cohort_size) >= 0)

    def test_report_result_sum_only_csv(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name' : self.cohort.name,
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

        response = self.client.post('/reports/create/', data=dict(
            responses=json_to_post
        ))

        # Wait a second for the task to get processed
        time.sleep(1)

        # Check that the task has been created
        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)

        # Check the csv result
        response = self.client.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find('Sum,,,8.0') >= 0)

    def test_report_result_std_dev_only_csv(self):
        # Make the request
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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

        response = self.client.post('/reports/create/', data=dict(
            responses=json_to_post
        ))

        # Wait a second for the task to get processed
        time.sleep(1)

        # Check that the task has been created
        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)

        # Check the csv result
        response = self.client.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find('Standard Deviation') >= 0)

    def test_save_public_report(self):
        fake_path = "fake_path"
        file_manager = PublicReportFileManager(self.logger, '/some/fake/absolute/path')
        file_manager.write_data = Mock()
        file_manager.remove_file = Mock()
        file_manager.get_public_report_path = MagicMock(return_value=fake_path)

        with file_manager_set(app, file_manager):

            desired_responses = [{
                'name': 'Edits - test',
                'cohort': {
                    'id': self.cohort.id,
                    'name': self.cohort.name,
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

            response = self.client.post('/reports/create/', data=dict(
                responses=json_to_post
            ))

            # Wait a second for the task to get processed
            time.sleep(1)

            # Check that the task has been created
            response = self.client.get('/reports/list/')
            parsed = json.loads(response.data)
            result_key = parsed['reports'][-1]['result_key']
            task, report = get_celery_task(result_key)
            assert_true(task and report)

            # Make the report publically accessible (save it to static/public)
            response = self.client.post('/reports/set-public/{}'.format(report.id))
            assert_true(response.status_code == 200)
            assert_equal(file_manager.write_data.call_count, 1)

            # Now make the report private (remove it from static/public)
            response = self.client.post('/reports/unset-public/{}'.format(report.id))
            assert_true(response.status_code == 200)
            file_manager.remove_file.assert_called_with(fake_path)
            assert_equal(file_manager.remove_file.call_count, 1)

    def test_report_result_timeseries_csv(self):

        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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

        response = self.client.post('/reports/create/', data=dict(
            responses=json_to_post
        ))

        # Wait a second for the task to get processed
        time.sleep(1)

        # Check that the task has been created
        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)

        # Check the csv result
        response = self.client.get('/reports/result/{0}.csv'.format(result_key))

        '''
        TODO
        csv format now looks like:
        Cohort,test-specific-cohort,,,,,
        Cohort Size,4,,,,,
        Created On,2014-03-14 17:26:55,,,,,
        Metric,NamespaceEdits,,,,,
        Metric_aggregateAverage,True,,,,,
        Metric_aggregateResults,True,,,,,
        Metric_aggregateStandardDeviation,False,,,,,
        Metric_aggregateSum,False,,,,,
        Metric_end_date,2013-05-01 00:00:00,,,,,
        Metric_individualResults,True,,,,,
        Metric_namespaces,"[0, 1, 2]",,,,,
        Metric_start_date,2013-01-01 00:00:00,,,,,
        Metric_timeseries,month,,,,,
        '''

        assert_true(response.data.find(
            'user_id,user_name,project,submetric,'
            '2013-01-01 00:00:00,2013-02-01 00:00:00,'
            '2013-03-01 00:00:00,2013-04-01 00:00:00'
        ) >= 0)
        assert_true(response.data.find(
            '{0},{1},{2},edits,1,2,1,0'.format(
                self.editors[0].user_id, self.editors[0].user_name, mediawiki_project)
        ) >= 0)
        assert_true(response.data.find(
            '{0},{1},{2},edits,1,2,1,0'.format(
                self.editors[1].user_id, self.editors[1].user_name, mediawiki_project)
        ) >= 0)
        assert_true(response.data.find(
            'Average,,,edits,0.5000,1.0000,0.5000,0.0000'
        ) >= 0)

        # Testing to see if the parameters are also in the CSV
        assert_true(response.data.find('parameters') >= 0)
        assert_true(response.data.find('start_date') >= 0)
        assert_true(response.data.find('end_date') >= 0)
        assert_true(response.data.find('namespaces') >= 0)
        cohort_size = 'Cohort Size,{0}'.format(len(self.cohort))
        assert_true(response.data.find(cohort_size) >= 0)

    @raises(InvalidCohort)
    def test_report_does_not_run_on_invalid_cohort(self):

        self.cohort.validated = False
        self.session.commit()

        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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

        self.client.post('/reports/create/', data=dict(
            responses=json_to_post
        ))


class MultiProjectTests(ControllerAsyncTest):
    
    def setUp(self):
        ControllerAsyncTest.setUp(self)
        
        # Prepare the second wiki database by adding a user with the same id as editor 0
        self.mwSession2.add(MediawikiUser(
            user_id=self.editors[0].user_id,
            user_name='',
        ))
        self.mwSession2.commit()
        
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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
        self.json_to_post = json.dumps(desired_responses)
    
    def test_user_in_two_projects(self):
        same_name_different_project = WikiUserStore(
            mediawiki_userid=self.editors[0].user_id,
            mediawiki_username='Editor 0 in second wiki',
            project=second_mediawiki_project,
            valid=True,
            validating_cohort=self.cohort.id,
        )
        self.session.add(same_name_different_project)
        self.session.commit()
        self.session.add(CohortWikiUserStore(
            cohort_id=self.cohort.id,
            wiki_user_id=same_name_different_project.id,
        ))
        self.session.commit()
        
        response = self.client.post('/reports/create/', data=dict(
            responses=self.json_to_post
        ))
        
        # Wait a second for the task to get processed
        time.sleep(1)
        
        # Check that the task has been created
        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        # Check the csv result
        response = self.client.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find(
            '{0},{1},{2},edits,0,0,0,0'.format(
                self.editors[0].user_id, 'Editor 0 in second wiki',
                second_mediawiki_project)
        ) >= 0)
    
    def test_two_users_same_id_same_cohort(self):
        same_id_same_cohort = WikiUserStore(
            mediawiki_userid=self.editors[0].user_id,
            mediawiki_username='Editor X with same id',
            project=second_mediawiki_project,
            valid=True,
            validating_cohort=self.cohort.id,
        )
        self.session.add(same_id_same_cohort)
        self.session.commit()
        self.session.add(CohortWikiUserStore(
            cohort_id=self.cohort.id,
            wiki_user_id=same_id_same_cohort.id,
        ))
        self.session.commit()
        
        response = self.client.post('/reports/create/', data=dict(
            responses=self.json_to_post
        ))
        
        # Wait a second for the task to get processed
        time.sleep(1)
        
        # Check that the task has been created
        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        # Check the csv result
        response = self.client.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find(
            '{0},{1},{2},edits,0,0,0,0'.format(
                self.editors[0].user_id, 'Editor X with same id',
                second_mediawiki_project)
        ) >= 0)
    
    def test_two_users_same_id_different_cohort(self):
        second_cohort = CohortStore(
            name='second-cohort',
            enabled=True,
            public=False,
            validated=True,
        )
        self.session.add(second_cohort)
        same_id_different_cohort = WikiUserStore(
            mediawiki_userid=self.editors[0].user_id,
            mediawiki_username='Editor X should not show up',
            project=second_mediawiki_project,
            valid=True,
            validating_cohort=second_cohort.id,
        )
        self.session.add(same_id_different_cohort)
        self.session.commit()
        self.session.add(CohortWikiUserStore(
            cohort_id=second_cohort.id,
            wiki_user_id=same_id_different_cohort.id,
        ))
        self.session.commit()
        
        response = self.client.post('/reports/create/', data=dict(
            responses=self.json_to_post
        ))
        
        # Wait a second for the task to get processed
        time.sleep(1)
        
        # Check that the task has been created
        response = self.client.get('/reports/list/')
        parsed = json.loads(response.data)
        result_key = parsed['reports'][-1]['result_key']
        task, report = get_celery_task(result_key)
        # Check the csv result
        response = self.client.get('/reports/result/{0}.csv'.format(result_key))
        assert_true(response.data.find(
            '{0},{1},{2}edits,0,0,0,0'.format(
                self.editors[0].user_id, 'Editor X should not show up',
                second_mediawiki_project)
        ) < 0)


class BasicTests(unittest.TestCase):

    def test_get_celery_task_no_key(self):
        (r1, r2) = get_celery_task(None)
        assert_equal(r1, None)
        assert_equal(r2, None)

    def test_get_celery_task_result_when_invalid(self):
        mock_report = ReportStore()
        failure = mock_report.get_result_safely('')
        assert_equal(failure['failure'], 'result not available')
    
    def test_get_celery_task_result_when_empty(self):
        mock_report = ReportStore()
        failure = mock_report.get_result_safely('')
        assert_equal(failure['failure'], 'result not available')
