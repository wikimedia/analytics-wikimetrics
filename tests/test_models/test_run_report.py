from nose.tools import assert_equals, assert_true, raises
from celery.exceptions import SoftTimeLimitExceeded
from tests.fixtures import QueueDatabaseTest
from wikimetrics.models import (
    RunReport, Aggregation, PersistentReport
)
from wikimetrics.metrics import TimeseriesChoices


class RunReportTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_empty_response(self):
        # TODO: handle case where user tries to submit form with no cohorts / metrics
        jr = RunReport([], user_id=self.owner_user_id)
        result = jr.task.delay(jr).get()
        assert_equals(result, [])
    
    def test_basic_response(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-01-02 00:00:00',
                'individualResults': True,
                'aggregateResults': False,
                'aggregateSum': False,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == jr.children[0].persistent_id)\
            .one()\
            .result_key
        results = results[result_key]
        # TODO: figure out why one of the resulting wiki_user_ids is None here
        assert_equals(
            results[Aggregation.IND][0][self.editors[0].user_id]['edits'],
            2,
        )
    
    def test_aggregated_response_namespace_edits(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-01-02 00:00:00',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == jr.children[0].persistent_id)\
            .one()\
            .result_key
        results = results[result_key]
        assert_equals(
            results[Aggregation.IND][0][self.editors[0].user_id]['edits'],
            2,
        )
        
        assert_equals(
            results[Aggregation.SUM]['edits'],
            4,
        )
    
    def test_aggregated_response_namespace_edits_with_timeseries(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:20:00',
                'end_date': '2013-03-01 00:00:00',
                'timeseries': TimeseriesChoices.MONTH,
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == jr.children[0].persistent_id)\
            .one()\
            .result_key
        results = results[result_key]
        
        user_id = self.editors[0].user_id
        key = results[Aggregation.IND][0][user_id]['edits'].items()[0][0]
        assert_equals(key, '2013-01-01 00:20:00')
        
        assert_equals(
            results[Aggregation.SUM]['edits'].items()[0][0],
            '2013-01-01 00:20:00',
        )
        
        assert_equals(
            results[Aggregation.SUM]['edits']['2013-01-01 00:20:00'],
            8,
        )
        assert_equals(
            results[Aggregation.SUM]['edits']['2013-02-01 00:00:00'],
            2,
        )
    
    # TODO: This is weird, the exception seems to be thrown
    # But the line is still showing as not covered by tests
    @raises(Exception)
    def test_invalid_metric(self):
        run_report = RunReport()
        run_report.parse_request([{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': 'blah blah',
            },
        }])
    
    def test_run_report_finish(self):
        run_report = RunReport([])
        result = run_report.finish([])
        assert_equals(result[run_report.result_key], 'Finished')
    
    def test_run_report_repr(self):
        run_report = RunReport([])
        assert_true(str(run_report).find('RunReport') >= 0)


class RunReportBytesTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_2()
    
    def test_aggregated_response_bytes_added(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'BytesAdded',
                'namespaces': [0],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-01-03 00:00:00',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
        }]
        jr = RunReport(desired_responses, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == jr.children[0].persistent_id)\
            .one()\
            .result_key
        results = results[result_key]
        assert_equals(
            results[Aggregation.IND][0][self.editors[0].user_id]['net_sum'],
            -90,
        )
        
        assert_equals(
            results[Aggregation.SUM]['positive_only_sum'],
            140,
        )
    
    # TODO: figure out how to write this test properly,
    # basically: how to make sure that the queue can be hamerred with requests
    def test_lots_of_concurrent_requests(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'BytesAdded',
                'namespaces': '0,1,2',
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-01-02 00:00:00',
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
            jr = RunReport(desired_responses, user_id=self.owner_user_id)
            reports.append((jr, jr.task.delay(jr)))
        
        successes = 0
        for jr, delayed in reports:
            try:
                results = delayed.get()
                self.session.commit()
                result_key = self.session.query(PersistentReport)\
                    .filter(PersistentReport.id == jr.children[0].persistent_id)\
                    .one()\
                    .result_key
                results = results[result_key]
                if results[Aggregation.SUM]['positive_only_sum'] == 140:
                    successes += 1
            except SoftTimeLimitExceeded:
                print('Timeout expired during this task.')
            except Exception:
                print('An exception occurred during this task.')
                raise
        
        print('Successes: {0}'.format(successes))
        assert_true(successes == trials, 'all of the trials must succeed')
