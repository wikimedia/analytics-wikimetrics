from nose.tools import assert_true
from tests.fixtures import DatabaseTest, QueueDatabaseTest

from wikimetrics.metrics import RandomMetric
from wikimetrics.models import MetricReport


class DummyTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_1(self):
        metric = RandomMetric()
        results = metric(self.editor_ids, self.mwSession)
        
        assert_true(results[results.keys()[0]] > 1000)


class DummyQueueTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_1(self):
        metric = RandomMetric()
        report = MetricReport(metric, self.cohort.id, self.editor_ids, self.project)
        results = report.task.delay(report).get()
        
        assert_true(results[results.keys()[0]] > 1000)
