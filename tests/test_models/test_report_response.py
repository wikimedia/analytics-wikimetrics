from wikimetrics.models import Cohort, RunReport, MultiProjectMetricReport
from wikimetrics.metrics import NamespaceEdits
from ..fixtures import QueueDatabaseTest
from nose.tools import assert_equals, assert_true


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
                'namespaces': '0,1,2',
                'individualResults': True,
                'aggregateResults': False,
                'aggregateSum': False,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.test_user_id)
        results = jr.task.delay(jr).get()[0]
        # TODO: figure out why one of the resulting wiki_user_ids is None here
        assert_equals(
            results['individual results'][0][self.test_mediawiki_user_id]['edits'],
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
                'namespaces': '0,1,2',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.test_user_id)
        results = jr.task.delay(jr).get()[0]
        assert_equals(
            results['individual results'][0][self.test_mediawiki_user_id]['edits'],
            2,
        )
        
        assert_equals(
            results['Sum']['edits'],
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
                'namespaces': '0,1,2',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.test_user_id)
        results = jr.task.delay(jr).get()[0]
        assert_equals(
            results['individual results'][0][self.test_mediawiki_user_id]['net_sum'],
            10,
        )
        
        assert_equals(
            results['Sum']['positive_only_sum'],
            50,
        )
    
    def test_lots_of_concurrent_requests(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.test_cohort_id,
            },
            'metric': {
                'name': 'BytesAdded',
                'namespaces': '0,1,2',
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
        for i in range(6):
            jr = RunReport(desired_responses, user_id=self.test_user_id)
            reports.append(jr.task.delay(jr))
        
        successes = 0
        for report in reports:
            try:
                results = report.get()[0]
                if results['Sum']['positive_only_sum'] == 50:
                    successes += 1
            except:
                print('timeout expired for this task')
        
        assert_true(successes > 3, 'at least half of the tasks succeeded')
