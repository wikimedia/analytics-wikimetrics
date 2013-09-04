from nose.tools import assert_equals, assert_true
from wikimetrics.metrics import metric_classes
from wikimetrics.models import (
    MultiProjectMetricReport, PersistentReport, Cohort,
)
from ..fixtures import QueueDatabaseTest, DatabaseTest


class MultiProjectMetricReportTest(QueueDatabaseTest):
    
    def test_basic_response(self):
        cohort = self.session.query(Cohort).get(self.test_cohort_id)
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-06-01',
            end_date='2013-09-01',
        )
        mr = MultiProjectMetricReport(cohort, metric, 'enwiki')
        
        result = mr.task.delay(mr).get()
        
        self.session.commit()
        result_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == mr.persistent_id)\
            .one()\
            .result_key
        
        assert_equals(result[result_key][self.test_mediawiki_user_id]['edits'], 2)


class MultiProjectMetricReportWithoutQueueTest(DatabaseTest):
    
    def test_finish(self):
        cohort = self.session.query(Cohort).get(self.test_cohort_id)
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-06-01',
            end_date='2013-09-01',
        )
        mr = MultiProjectMetricReport(cohort, metric, 'enwiki')
        
        finished = mr.finish([
            {
                1: {'edits': 2},
                2: {'edits': 3},
                3: {'edits': 0},
                None: {'edits': 0}
            }
        ])
        
        assert_equals(finished[mr.result_key][1]['edits'], 2)
        assert_equals(finished[mr.result_key][2]['edits'], 3)
    
    def test_repr(self):
        cohort = self.session.query(Cohort).get(self.test_cohort_id)
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-06-01',
            end_date='2013-09-01',
        )
        mr = MultiProjectMetricReport(cohort, metric, 'enwiki')
        
        assert_true(str(mr).find('MultiProjectMetricReport') >= 0)
