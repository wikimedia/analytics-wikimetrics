from nose.tools import assert_not_equals
from tests.fixtures import QueueTest
from wikimetrics.models import MetricReport
from wikimetrics.metrics import RandomMetric


class AsyncTaskTest(QueueTest):
    
    def test_submit_task(self):
        metric = RandomMetric()
        report = MetricReport(metric, [1, 2], 'enwiki')
        async_result = report.task.delay(report)
        
        # .get() blocks until task finishes executing
        sync_result = async_result.get()
        assert_not_equals(
            sync_result[1],
            None,
            'task did not run on celery queue'
        )
