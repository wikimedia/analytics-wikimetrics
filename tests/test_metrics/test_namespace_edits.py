from datetime import datetime
from nose.tools import assert_true, assert_equal
from tests.fixtures import DatabaseWithCohortTest, QueueDatabaseTest, DatabaseTest

from wikimetrics.metrics import NamespaceEdits, TimeseriesChoices
from wikimetrics.models import Cohort, MetricReport


class NamespaceEditsDatabaseTest(DatabaseWithCohortTest):
    
    def test_finds_edits(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-05-01 00:00:00',
            end_date='2013-08-01 00:00:00',
        )
        results = metric(list(self.cohort), self.mwSession)
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id]['edits'], 2)
        assert_equal(results[self.test_mediawiki_user_id_evan]['edits'], 3)
    
    def test_reports_zero_edits(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-05-01 00:00:00',
            end_date='2013-08-01 00:00:00',
        )
        results = metric(list(self.cohort), self.mwSession)
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id_andrew]['edits'], 0)

    def test_uses_date_range(self):
        
        metric = NamespaceEdits(
            namespaces=[0],
        )
        assert_true(not metric.validate())
        
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-06-30 00:00:00',
            end_date='2013-07-01 00:00:00',
        )
        metric.fake_csrf()
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
        print results
        assert_equal(results[self.dan_id]['edits'], 1)


class NamespaceEditsFullTest(QueueDatabaseTest):
    
    def test_namespace_edits(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-05-01 00:00:00',
            end_date='2013-08-01 00:00:00',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id_evan]['edits'], 3)
    
    def test_namespace_edits_namespace_filter(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces=[3],
            start_date='2013-05-01 00:00:00',
            end_date='2013-08-01 00:00:00',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id_evan]['edits'], 0)
    
    def test_namespace_edits_namespace_filter_no_namespace(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces=[],
            start_date='2013-05-01 00:00:00',
            end_date='2013-08-01 00:00:00',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id_evan]['edits'], 0)
    
    def test_namespace_edits_with_multiple_namespaces(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces=[0, 209],
            start_date='2013-05-01 00:00:00',
            end_date='2013-08-06 00:00:00',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id]['edits'], 3)
    
    def test_namespace_edits_with_multiple_namespaces_when_passing_string_list(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces='0, 209',
            start_date='2013-05-01 00:00:00',
            end_date='2013-08-06 00:00:00',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id]['edits'], 3)


class NamespaceEditsTimeseriesTest(DatabaseTest):
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=4,
            revisions_per_editor=3,
            revision_timestamps=[
                [20121231230000, 20130101003000, 20130101010000],
                [20130101120000, 20130102000000, 20130102120000],
                [20130101000000, 20130108000000, 20130116000000],
                [20130101000000, 20130201000000, 20140101000000],
            ],
            revision_lengths=10
        )
    
    def test_the_setup_worked(self):
        assert_equal(len(self.editors), 4)
        assert_equal(len(self.revisions), 12)
        assert_equal(self.revisions[-1].rev_timestamp, datetime(2014, 01, 01))
        assert_equal(self.revisions[0].rev_timestamp, datetime(2012, 12, 31, 23))
    
    def test_timeseries_by_day(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2012-12-31 00:00:00',
            end_date='2014-01-02 00:00:00',
            timeseries=TimeseriesChoices.DAY,
        )
        results = metric(list(self.cohort), self.mwSession)
        
        assert_equal(results[self.editors[0].user_id]['edits'], 3)


class NamespaceEditsTimestampTest(DatabaseTest):
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=1,
            revisions_per_editor=5,
            revision_timestamps=[[
                20130101000000,
                20130101010000,
                20130101010100,
                20130101020100,
                20130101020101,
            ]],
            revision_lengths=10
        )
    
    def test_timestamp_range_hour(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-01 01:00:00',
        )
        results = metric(list(self.cohort), self.mwSession)
        assert_equal(results[self.editors[0].user_id]['edits'], 1)
        
    def test_timestamp_range_minutes(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-01 01:01:00',
        )
        results = metric(list(self.cohort), self.mwSession)
        assert_equal(results[self.editors[0].user_id]['edits'], 2)
        
    def test_timestamp_range_seconds(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-01-01 02:01:00',
            end_date='2013-01-01 02:01:01',
        )
        results = metric(list(self.cohort), self.mwSession)
        assert_equal(results[self.editors[0].user_id]['edits'], 1)
