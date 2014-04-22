from nose.tools import assert_equals, assert_true
from wikimetrics.metrics import metric_classes
from wikimetrics.models import (
    MultiProjectMetricReport, PersistentReport, Cohort,
)
from ..fixtures import QueueDatabaseTest, DatabaseTest


class MultiProjectMetricReportTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_basic_response(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-02 00:00:00',
        )
        mr = MultiProjectMetricReport(self.cohort, metric)
        
        result = mr.task.delay(mr).get()
        
        assert_equals(result[self.editor(0)]['edits'], 2)


class MultiProjectMetricReportWithoutQueueTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_finish(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-05-01 00:00:00',
            end_date='2013-09-01 00:00:00',
        )
        mr = MultiProjectMetricReport(self.cohort, metric)
        
        finished = mr.finish([
            {
                1: {'edits': 2},
                2: {'edits': 3},
                3: {'edits': 0},
                None: {'edits': 0}
            }
        ])
        
        assert_equals(finished[1]['edits'], 2)
        assert_equals(finished[2]['edits'], 3)
    
    def test_repr(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-05-01 00:00:00',
            end_date='2013-09-01 00:00:00',
        )
        mr = MultiProjectMetricReport(self.cohort, metric)
        
        assert_true(str(mr).find('MultiProjectMetricReport') >= 0)
