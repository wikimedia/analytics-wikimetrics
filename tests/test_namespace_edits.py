from nose.tools import *
from fixtures import DatabaseTest, QueueDatabaseTest

from wikimetrics.metrics import NamespaceEdits
from wikimetrics.models import Cohort, MetricJob


class NamespaceEditsDatabaseTest(DatabaseTest):
    def setUp(self):
        super(NamespaceEditsDatabaseTest, self).setUp()
        #TODO: add data for metric to find
        #mwSession.add(Revision(page_id=1,rev_user=
    
    
    def test_finds_edits(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits()
        results = metric(list(cohort), self.mwSession)
        
        assert_true(results is not None)
        assert_true(results['1'] == 2, 'Dan had not 2 edits')
        assert_true(results['2'] == 3, 'Evan had not 3 edits')
    
    
    def test_reports_zero_edits(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits()
        results = metric(list(cohort), self.mwSession)
        
        assert_true(results is not None)
        assert_true(results['3'] == 0, 'Andrew had not 0 edits')
    
    
    def test_reports_undefined(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits()
        results = metric(list(cohort), self.mwSession)
        
        assert_true(results is not None)
        assert_true(results['4'] is None, 'Diederik had not undefined edits')

class NamesapceEditsFullTest(QueueDatabaseTest):

    def test_namespace_edits(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()

        metric = NamespaceEdits()
        project = 'enwiki'
        metric_job = MetricJob(metric, list(cohort), project)
        metric_run_res = metric_job.run(metric_job)
        print 'metric_job.run(metric_job): %s' % metric_run_res
        async_result = metric_run_res.delay()
        results = async_result.get()

        assert_true(results is not None)
        assert_true(results['2'] == 3, 'Evan had not 3 edits, when run on queue')


    def test_namespace_edits_namespace_filter(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()

        namespaces = [3]
        metric = NamespaceEdits(namespaces)
        metric_job = MetricJob(metric, list(cohort), project)
        results = metric_job.get()

        assert_true(results is not None)
        assert_true(results['2'] == 0, 'Evan had not 0 edits in namespaces %d, when run on queue')


    def test_namespace_edits_namespace_filter_no_namespace(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()

        namespaces = []
        metric = NamespaceEdits(namespaces)
        metric_job = MetricJob(metric, list(cohort), project)
        results = metric_job.get()

        assert_true(results is not None)
        assert_true(results['2'] == 0, 'Evan had not 0 edits in namespaces %s, when run on queue')
