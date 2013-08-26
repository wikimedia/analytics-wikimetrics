from nose.tools import assert_true, assert_equal
from tests.fixtures import DatabaseWithCohortTest, QueueDatabaseTest

from wikimetrics.metrics import NamespaceEdits
from wikimetrics.models import Cohort, MetricReport


class NamespaceEditsDatabaseTest(DatabaseWithCohortTest):
    
    def test_finds_edits(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-06-01',
            end_date='2013-08-01',
        )
        results = metric(list(self.cohort), self.mwSession)
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id]['edits'], 2)
        assert_equal(results[self.test_mediawiki_user_id_evan]['edits'], 3)
    
    def test_reports_zero_edits(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2013-06-01',
            end_date='2013-08-01',
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
            start_date='2013-07-01',
            end_date='2013-07-02',
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
            start_date='2013-06-01',
            end_date='2013-08-01',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        print 'results: %s' % results
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id_evan]['edits'], 3)
    
    def test_namespace_edits_namespace_filter(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces=[3],
            start_date='2013-06-01',
            end_date='2013-08-01',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id_evan]['edits'], 0)
    
    def test_namespace_edits_namespace_filter_no_namespace(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces=[],
            start_date='2013-06-01',
            end_date='2013-08-01',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id_evan]['edits'], 0)
    
    def test_namespace_edits_with_multiple_namespaces(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces=[0, 209],
            start_date='2013-06-01',
            end_date='2013-08-06',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id]['edits'], 3)
    
    def test_namespace_edits_with_multiple_namespaces_when_passing_string_list(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits(
            namespaces='0, 209',
            start_date='2013-06-01',
            end_date='2013-08-06',
        )
        report = MetricReport(metric, list(cohort), 'enwiki')
        results = report.task.delay(report).get()
        
        assert_true(results is not None)
        assert_equal(results[self.test_mediawiki_user_id]['edits'], 3)
