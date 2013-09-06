from nose.tools import assert_equals, assert_true
from wikimetrics.metrics import metric_classes
from wikimetrics.models import (
    MetricReport
)
from ..fixtures import DatabaseTest


class MetricReportTest(DatabaseTest):
    
    def test_basic_response(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-06-01 00:00:00',
            end_date='2013-09-01 00:00:00',
        )
        mr = MetricReport(
            metric,
            [
                self.test_mediawiki_user_id,
                self.test_mediawiki_user_id_evan,
                self.test_mediawiki_user_id_andrew,
            ],
            'enwiki'
        )
        
        result = mr.run()
        assert_equals(result[self.test_mediawiki_user_id]['edits'], 2)
    
    def test_repr(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-06-01 00:00:00',
            end_date='2013-09-01 00:00:00',
        )
        mr = MetricReport(
            metric,
            [
                self.test_mediawiki_user_id,
                self.test_mediawiki_user_id_evan,
                self.test_mediawiki_user_id_andrew,
            ],
            'enwiki'
        )
        
        assert_true(str(mr).find('MetricReport') >= 0)
