import time
from datetime import timedelta, datetime
from sqlalchemy import func
from nose.tools import assert_equals, assert_true, raises
from nose.plugins.attrib import attr
from mock import MagicMock
from celery.exceptions import SoftTimeLimitExceeded

from tests.fixtures import QueueDatabaseTest, DatabaseTest
from wikimetrics.models import RunReport, ReportStore, WikiUserStore, CohortWikiUserStore
from wikimetrics.exceptions import InvalidCohort
from wikimetrics.metrics import TimeseriesChoices, metric_classes
from wikimetrics.utils import diff_datewise, stringify, strip_time
from wikimetrics.enums import Aggregation
from wikimetrics.configurables import queue
from wikimetrics.schedules.daily import recurring_reports


class RunReportClassMethodsTest(DatabaseTest):
    def tearDown(self):
        # re-enable the scheduler after these tests
        queue.conf['CELERYBEAT_SCHEDULE'] = self.save_schedule

    def setUp(self):
        DatabaseTest.setUp(self)

        # turn off the scheduler for this test
        self.save_schedule = queue.conf['CELERYBEAT_SCHEDULE']
        queue.conf['CELERYBEAT_SCHEDULE'] = {}

        self.common_cohort_1()
        self.uid = self.owner_user_id
        self.today = strip_time(datetime.today())
        # NOTE: running with 20 just makes the tests run faster, but any value > 11 works
        self.no_more_than = 20
        self.missed_by_index = {
            0: [1, 2, 11],
            1: [1, 2, 11, self.no_more_than + 1, self.no_more_than + 3],
            2: [1, 2],
            3: range(0, self.no_more_than + 10),
        }
        self.ago_by_index = {
            0: 26,
            1: self.no_more_than + 10,
            2: 6,
            3: self.no_more_than + 10
        }
        age = {
            i: self.today - timedelta(days=v - 1)
            for i, v in self.ago_by_index.items()
        }

        self.p = {
            'metric': {
                'start_date': age[0], 'end_date': self.today, 'name': 'NamespaceEdits',
            },
            'recurrent': True,
            'cohort': {'id': self.cohort.id, 'name': self.cohort.name},
            'name': 'test-recurrent-reports',
        }
        ps = stringify(self.p)

        self.reports = [
            ReportStore(recurrent=True, created=age[0], parameters=ps, user_id=self.uid),
            ReportStore(recurrent=True, created=age[1], parameters=ps, user_id=self.uid),
            ReportStore(recurrent=True, created=age[2], parameters=ps, user_id=self.uid),
            ReportStore(recurrent=True, created=age[3], parameters=ps, user_id=self.uid),
        ]
        self.session.add_all(self.reports)
        self.session.commit()

    def add_runs_to_report(self, index):
        p = self.p
        self.report_runs = []
        for d in range(0, self.no_more_than + 10):
            day = self.today - timedelta(days=d)
            p['metric']['start_date'] = day - timedelta(days=1)
            p['metric']['end_date'] = day
            p['recurrent'] = False
            ps = stringify(p)
            if d not in (self.missed_by_index[index]) and d < self.ago_by_index[index]:
                self.report_runs.append(ReportStore(
                    recurrent_parent_id=self.reports[index].id,
                    created=day,
                    status='SUCCESS',
                    parameters=ps,
                    user_id=self.uid,
                ))

        self.session.add_all(self.report_runs)
        self.session.commit()

    def test_days_missed_0(self):
        self.add_runs_to_report(0)
        missed_days = RunReport.days_missed(self.reports[0], self.session)
        assert_equals(set(missed_days), set([
            self.today - timedelta(days=m)
            for m in self.missed_by_index[0]
        ]))

    def test_days_missed_1(self):
        self.add_runs_to_report(1)
        missed_days = RunReport.days_missed(self.reports[1], self.session)
        assert_equals(set(missed_days), set([
            self.today - timedelta(days=m)
            for m in self.missed_by_index[1]
        ]))

    def test_days_missed_2(self):
        self.add_runs_to_report(2)
        missed_days = RunReport.days_missed(self.reports[2], self.session)
        assert_equals(set(missed_days), set([
            self.today - timedelta(days=m)
            for m in self.missed_by_index[2]
        ]))

    def test_create_reports_for_missed_days_0(self):
        self.add_runs_to_report(0)
        new_runs = list(RunReport.create_reports_for_missed_days(
            self.reports[0], self.session, no_more_than=self.no_more_than
        ))
        assert_equals(set([r.created for r in new_runs]), set([
            self.today - timedelta(days=m)
            for m in self.missed_by_index[0]
        ]))

    def test_create_reports_for_missed_days_1(self):
        self.add_runs_to_report(1)
        new_runs = list(RunReport.create_reports_for_missed_days(
            self.reports[1], self.session, no_more_than=self.no_more_than
        ))
        assert_equals(set([r.created for r in new_runs]), set([
            self.today - timedelta(days=m)
            for m in self.missed_by_index[1]
        ]))

    def test_create_reports_for_missed_days_2(self):
        self.add_runs_to_report(2)
        new_runs = list(RunReport.create_reports_for_missed_days(
            self.reports[2], self.session, no_more_than=self.no_more_than
        ))
        assert_equals(set([r.created for r in new_runs]), set([
            self.today - timedelta(days=m)
            for m in self.missed_by_index[2]
        ]))

    def test_create_reports_for_missed_days_3(self):
        self.add_runs_to_report(3)
        new_runs = list(RunReport.create_reports_for_missed_days(
            self.reports[3], self.session, no_more_than=self.no_more_than
        ))
        assert_equals(len(new_runs), self.no_more_than)


class RunReportTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_1()

    @raises(Exception)
    def test_empty_response(self):
        """
        Case where user tries to submit form with no cohorts / metrics
        should be handled client side server side an exception will be
        thrown if RunReport object cannot be created
        """
        RunReport({}, user_id=self.owner_user_id)

    def test_basic_response(self):
        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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
        }
        jr = RunReport(parameters, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(ReportStore) \
            .get(jr.persistent_id) \
            .result_key
        results = results[result_key]
        # TODO: figure out why one of the resulting wiki_user_ids is None here
        assert_equals(
            results[Aggregation.IND][self.editor(0)]['edits'],
            2,
        )

    def test_raises_invalid_cohort_for_any_metric(self):
        self.cohort.validated = False
        self.session.commit()

        for name, metric in metric_classes.iteritems():
            if not metric.show_in_ui:
                continue

            parameters = {
                'name': '{0} - test'.format(name),
                'cohort': {
                    'id': self.cohort.id,
                    'name': self.cohort.name,
                },
                'metric': {
                    'name': name,
                    'namespaces': [0, 1, 2],
                    'start_date': '2013-01-01 00:00:00',
                    'end_date': '2013-01-02 00:00:00',
                    'individualResults': True,
                    'aggregateResults': False,
                    'aggregateSum': False,
                    'aggregateAverage': False,
                    'aggregateStandardDeviation': False,
                },
            }
            try:
                RunReport(parameters, user_id=self.owner_user_id)
            except InvalidCohort:
                continue
            assert_true(False)

    def test_wiki_cohort_runs(self):
        self.create_wiki_cohort()
        # give the WikiCohort all the users of self.cohort, for easy testing
        self.session.execute(
            WikiUserStore.__table__.update().values(
                validating_cohort=self.basic_wiki_cohort.id
            ).where(
                WikiUserStore.validating_cohort == self.cohort.id
            )
        )
        self.session.execute(
            CohortWikiUserStore.__table__.update().values(
                cohort_id=self.basic_wiki_cohort.id
            ).where(
                CohortWikiUserStore.cohort_id == self.cohort.id
            )
        )
        self.cohort = self.basic_wiki_cohort
        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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
        }
        jr = RunReport(parameters, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(ReportStore) \
            .get(jr.persistent_id) \
            .result_key
        results = results[result_key]
        assert_equals(
            results[Aggregation.IND][self.editor(0)]['edits'],
            2,
        )

        assert_equals(
            results[Aggregation.SUM]['edits'],
            4,
        )

    def test_aggregated_response_namespace_edits(self):
        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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
        }
        jr = RunReport(parameters, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(ReportStore) \
            .get(jr.persistent_id) \
            .result_key
        results = results[result_key]
        assert_equals(
            results[Aggregation.IND][self.editor(0)]['edits'],
            2,
        )

        assert_equals(
            results[Aggregation.SUM]['edits'],
            4,
        )

    def test_aggregated_response_namespace_edits_with_timeseries(self):
        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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
        }
        jr = RunReport(parameters, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(ReportStore) \
            .get(jr.persistent_id) \
            .result_key
        results = results[result_key]

        key = results[Aggregation.IND][self.editor(0)]['edits'].items()[0][0]
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
    def test_invalid_metric(self):
        jr = RunReport({
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': 'blah blah',
            },
        }, user_id=self.owner_user_id)

        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(ReportStore) \
            .get(jr.persistent_id) \
            .result_key
        assert_true(
            results[result_key]['FAILURE'].find('Edits was incorrectly configured') >= 0,
        )

    def test_first_run_of_recurrent_report_happens(self):
        '''
        Scheduling a recurrent report should run the 1st run of the report right away
        and not wait for the scheduled run
        '''

        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-01-03 00:00:00',
                'individualResults': True,
                'aggregateResults': False,
                'aggregateSum': False,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
            'recurrent': True,
            'public': True
        }

        # with patch.object(RunReport, '_run_child_report', mock_run):
        rr = RunReport(parameters, user_id=self.owner_user_id)
        rr._run_child_report = MagicMock()
        rr.task.delay(rr)
        rr._run_child_report.assert_called_once_with()


class RunReportBasicTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()

    @raises(KeyError)
    def test_invalid_report(self):
        RunReport({})

    def test_run_report_finish(self):
        run_report = RunReport({
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'NamespaceEdits',
            },
        }, user_id=self.owner_user_id)
        result = run_report.finish(['aggregate_result'])
        assert_equals(result[run_report.result_key], 'aggregate_result')

    def test_run_report_repr(self):
        run_report = RunReport({
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'NamespaceEdits',
            },
        }, user_id=self.owner_user_id)
        assert_true(str(run_report).find('RunReport') >= 0)


class RunReportBytesTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_2()

    def test_aggregated_response_bytes_added(self):
        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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
        }
        jr = RunReport(parameters, user_id=self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(ReportStore) \
            .get(jr.persistent_id) \
            .result_key
        results = results[result_key]
        assert_equals(
            results[Aggregation.IND][self.editor(0)]['net_sum'],
            -90,
        )

        assert_equals(
            results[Aggregation.SUM]['positive_only_sum'],
            140,
        )

    # TODO: figure out how to write this test properly,
    # basically: how to make sure that the queue can be hamerred with requests
    def test_lots_of_concurrent_requests(self):
        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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
        }
        reports = []
        # NOTE: you can make this loop as much as you'd like if celery
        # is allowed enough concurrent workers, set via CELERYD_CONCURRENCY
        trials = 3
        for i in range(trials):
            jr = RunReport(parameters, user_id=self.owner_user_id)
            reports.append((jr, jr.task.delay(jr)))

        successes = 0
        for jr, delayed in reports:
            try:
                results = delayed.get()
                self.session.commit()
                result_key = self.session.query(ReportStore) \
                    .get(jr.persistent_id) \
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


class RunReportScheduledTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_1()

    def test_scheduler(self):
        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-01-03 00:00:00',
                'individualResults': True,
                'aggregateResults': False,
                'aggregateSum': False,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
            'recurrent': True,
        }

        jr = RunReport(parameters, user_id=self.owner_user_id)
        jr.task.delay(jr).get()
        self.session.commit()

        # executing directly the code that will be run by the scheduler
        recurring_reports()
        recurrent_runs = self.session.query(ReportStore) \
            .filter(ReportStore.recurrent_parent_id == jr.persistent_id) \
            .all()

        # make sure we have one and no more than one recurrent run
        assert_equals(len(recurrent_runs), 1)

    def test_user_id_assigned_properly(self):
        parameters = {
            'name': 'Bytes - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
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
        }

        jr = RunReport(parameters, user_id=self.owner_user_id)
        jr.task.delay(jr).get()
        self.session.commit()
        # executing directly the code that will be run by the scheduler
        recurring_reports()

        # make sure all report nodes have a user_id
        no_user_id = self.session.query(func.count(ReportStore)) \
            .filter(ReportStore.user_id == None) \
            .one()[0]
        assert_equals(no_user_id, 0)
