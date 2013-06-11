from nose.tools import *
from fixtures import QueueTest
from wikimetrics.models import MetricJob
from wikimetrics.metrics import RandomMetric


class AsyncTaskTest(QueueTest):
    
    def test_submit_task(self):
        metric = RandomMetric()
        job = MetricJob(metric, [1,2], 'enwiki')
        async_result = job.run.delay(job)
        sync_result = async_result.get()
        assert_true(
            sync_result[1] is not None,
            'task did not run on celery queue'
        )
