import celery
from nose.tools import assert_equal, assert_true
from datetime import datetime

from wikimetrics.models import TaskErrorStore, ReportStore
from ..fixtures import DatabaseTest


class TaskErrorStoreTest(DatabaseTest):

    def setUp(self):
        DatabaseTest.setUp(self)
        self.report = ReportStore(status=celery.states.PENDING)
        self.session.add(self.report)
        self.session.commit()

    def test_add_new(self):
        # If the failing report has no previous errors,
        # a new task error should be created.
        t1 = datetime.now().replace(microsecond=0)
        TaskErrorStore.add('report', self.report.id, 'message', 'traceback')
        t2 = datetime.now().replace(microsecond=0)
        row = self.session.query(TaskErrorStore).first()
        assert_equal(row.task_type, 'report')
        assert_equal(row.task_id, self.report.id)
        assert_true(row.timestamp >= t1 and row.timestamp <= t2)
        assert_equal(row.message, 'message')
        assert_equal(row.traceback, 'traceback')
        assert_equal(row.count, 1)

    def test_add_existing(self):
        # If the failing report has previous errors,
        # the existing task error should be updated.
        t1 = datetime.now()
        te = TaskErrorStore(task_type='report', task_id=self.report.id, count=1,
                            timestamp=t1, message='message', traceback='traceback')
        self.session.add(te)
        self.session.commit()
        TaskErrorStore.add('report', self.report.id, 'message2', 'traceback2')
        t2 = datetime.now()
        row = self.session.query(TaskErrorStore).first()
        print t1, row.timestamp, t2
        assert_equal(row.task_type, 'report')
        assert_equal(row.task_id, self.report.id)
        assert_true(row.timestamp > t1 and row.timestamp < t2)
        assert_equal(row.message, 'message2')
        assert_equal(row.traceback, 'traceback2')
        assert_equal(row.count, 2)
