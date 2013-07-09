from nose.tools import assert_true
from tests.fixtures import DatabaseTest, QueueDatabaseTest

from wikimetrics import app
from wikimetrics.metrics import RandomMetric
from wikimetrics.models import Cohort, MetricJob


class DummyTest(DatabaseTest):
    
    def test_1(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = RandomMetric()
        results = metric(list(cohort), self.mwSession)
        
        assert_true(results[results.keys()[0]] > 1000)


class DummyQueueTest(QueueDatabaseTest):
    
    def test_1(self):
        cohort = self.session.query(Cohort).filter_by(name='test').one()
        
        metric = RandomMetric()
        job = MetricJob(metric, list(cohort), 'enwiki')
        results = job.run.delay().get()
        
        assert_true(results[results.keys()[0]] > 1000)
