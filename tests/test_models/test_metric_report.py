from nose.tools import assert_equals, assert_true
from wikimetrics.metrics import metric_classes
from wikimetrics.models import (
    MetricReport
)
from ..fixtures import DatabaseTest


class MetricReportTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_basic_response(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-02 00:00:00',
        )
        mr = MetricReport(
            metric,
            [
                self.editors[0].user_id,
                self.editors[1].user_id,
                self.editors[2].user_id,
            ],
            'enwiki'
        )
        
        result = mr.run()
        assert_equals(result[self.editors[0].user_id]['edits'], 2)
    
    def test_repr(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-05-01 00:00:00',
            end_date='2013-09-01 00:00:00',
        )
        mr = MetricReport(
            metric,
            [
                self.editors[0].user_id,
                self.editors[1].user_id,
                self.editors[2].user_id,
            ],
            'enwiki'
        )
        
        assert_true(str(mr).find('MetricReport') >= 0)
