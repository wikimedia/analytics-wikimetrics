from nose.tools import assert_equals, assert_true
from celery.exceptions import SoftTimeLimitExceeded
from wikimetrics.models import (
    Cohort, RunReport, MultiProjectMetricReport, Aggregation, PersistentReport
)
from wikimetrics.metrics import NamespaceEdits
from ..fixtures import QueueDatabaseTest


class RunReportTest(QueueDatabaseTest):
    
    def test_empty_response(self):
        # TODO: handle case where user tries to submit form with no cohorts / metrics
        jr = RunReport([], user_id=self.test_user_id)
        result = jr.task.delay(jr).get()
        assert_equals(result, [])
    
    def test_basic_response(self):
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
                'aggregateResults': False,
                'aggregateSum': False,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.test_user_id)
        results = jr.task.delay(jr).get()
        result_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == jr.children[0].persistent_id)\
            .one()\
            .result_key
        results = results[result_key]
        # TODO: figure out why one of the resulting wiki_user_ids is None here
        assert_equals(
            results[Aggregation.IND][0][self.test_mediawiki_user_id]['edits'],
            2,
        )
    
    def test_aggregated_response_namespace_edits(self):
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
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.test_user_id)
        results = jr.task.delay(jr).get()
        result_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == jr.children[0].persistent_id)\
            .one()\
            .result_key
        results = results[result_key]
        assert_equals(
            results[Aggregation.IND][0][self.test_mediawiki_user_id]['edits'],
            2,
        )
        
        assert_equals(
            results[Aggregation.SUM]['edits'],
            5,
        )
    
    def test_aggregated_response_bytes_added(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.test_cohort_id,
            },
            'metric': {
                'name': 'BytesAdded',
                'namespaces': [0, 1, 2],
                'start_date': '2013-06-01',
                'end_date': '2013-09-01',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.test_user_id)
        results = jr.task.delay(jr).get()
        result_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == jr.children[0].persistent_id)\
            .one()\
            .result_key
        results = results[result_key]
        assert_equals(
            results[Aggregation.IND][0][self.test_mediawiki_user_id]['net_sum'],
            6,
        )
        
        assert_equals(
            results[Aggregation.SUM]['positive_only_sum'],
            150,
        )
    
    # TODO: figure out how to write this test properly,
    # basically: how to make sure that the queue can be hamerred with requests
    def test_lots_of_concurrent_requests(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.test_cohort_id,
            },
            'metric': {
                'name': 'BytesAdded',
                'namespaces': '0,1,2',
                'start_date': '2013-06-01',
                'end_date': '2013-09-01',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        reports = []
        # NOTE: you can make this loop as much as you'd like if celery
        # is allowed enough concurrent workers, set via CELERYD_CONCURRENCY
        trials = 3
        for i in range(trials):
            jr = RunReport(desired_responses, user_id=self.test_user_id)
            reports.append((jr, jr.task.delay(jr)))
        
        successes = 0
        for jr, delayed in reports:
            try:
                results = delayed.get()
                result_key = self.session.query(PersistentReport)\
                    .filter(PersistentReport.id == jr.children[0].persistent_id)\
                    .one()\
                    .result_key
                results = results[result_key]
                if results[Aggregation.SUM]['positive_only_sum'] == 150:
                    successes += 1
            except SoftTimeLimitExceeded:
                print('Timeout expired during this task.')
            except Exception:
                print('An exception occurred during this task.')
                raise
        
        print('Successes: {0}'.format(successes))
        assert_true(successes == trials, 'all of the trials must succeed')
