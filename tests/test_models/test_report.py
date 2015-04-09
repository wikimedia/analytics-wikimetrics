# 101-108, 114, 130-145, 153
from nose.tools import assert_equals, assert_true, assert_raises
from wikimetrics.metrics import metric_classes
from wikimetrics.models import (
    Report, ReportNode, ReportLeaf, MetricReport, ReportStore, TaskErrorStore
)
from wikimetrics.models import queue_task
from ..fixtures import QueueDatabaseTest, DatabaseTest


class ReportTest(QueueDatabaseTest):
    
    # TODO: figure out a way to mock current_task so we can test ReportNode:run()
    #def test_report_node_run(self):
        
        #edits_metric = metric_classes['NamespaceEdits'](
            #name = 'NamespaceEdits',
            #namespaces = [0, 1, 2],
            #start_date = '2013-06-01',
            #end_date = '2013-09-01',
        #)
        #bytes_metric = metric_classes['NamespaceEdits'](
            #name = 'BytesAdded',
            #namespaces = [0, 1, 2],
            #start_date = '2013-06-01',
            #end_date = '2013-09-01',
        #)
        #children = [
            #MetricReport(edits_metric, 0, [self.test_mediawiki_user_id], 'wiki'),
            #MetricReport(bytes_metric, 0, [self.test_mediawiki_user_id], 'wiki'),
        #]
        #report_node = ReportNode(children=children)
        #results = report_node.run()
        
        #assert_equals(len(results), 2)
    
    def test_report_node_finish(self):
        report_node = ReportNode()
        report_node.finish([1, 2, 3])
        assert_true(True)
    
    def test_report_run(self):
        report = Report()
        report.run()
        assert_true(True)


class ReportWithoutQueueTest(DatabaseTest):
    
    def test_repr(self):
        r = Report()
        assert_true(str(r).find('Report') >= 0)


class QueueTaskTest(QueueDatabaseTest):
    
    def test_queue_task(self):
        fr = FakeReport()
        result = queue_task(fr)
        assert_equals(result, 'hello world')

    def test_queue_task_error(self):
        def raise_error():
            raise RuntimeError('message')

        fr = FakeReport(raise_error)
        assert_raises(RuntimeError, queue_task, fr)
        te = self.session.query(TaskErrorStore).first()
        assert_equals(te.task_id, fr.persistent_id)
        assert_equals(te.message, 'RuntimeError: message')
    
    def test_set_status(self):
        fr = FakeReport()
        fr.set_status('STARTED')
        self.session.commit()
        pr_started = self.session.query(ReportStore).get(fr.persistent_id)
        assert_equals(pr_started.status, 'STARTED')
        assert_equals(pr_started.queue_result_key, None)
    
    def test_set_status_and_task(self):
        fr = FakeReport()
        fr.set_status('WORKING', task_id=1)
        self.session.commit()
        pr_working = self.session.query(ReportStore).get(fr.persistent_id)
        assert_equals(pr_working.status, 'WORKING')
        assert_equals(pr_working.queue_result_key, '1')


class FakeReport(Report):
    """
    This just helps with some of the tests above
    """
    def __init__(self, callback=None):
        # store param must be True so that the result is retrievable
        # this param only defaults to True for RunReport
        super(FakeReport, self).__init__(store=True)
        self.callback = callback

    def run(self):
        if self.callback is None:
            return 'hello world'
        else:
            return self.callback()
