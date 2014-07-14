import time
from datetime import datetime, timedelta
from nose.tools import assert_true, assert_equal
from nose.plugins.attrib import attr
from tests.fixtures import DatabaseTest, i, d
from wikimetrics.configurables import queue
from wikimetrics.models import RunReport
from wikimetrics.models.storage import ReportStore
from wikimetrics.schedules.daily import recurring_reports


class ParallelReports(DatabaseTest):

    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()

        # ******* EXPERIMENT HERE
        # Before the fix in schedules/daily.py to increase max recursion:
        #   NO Max Recursion error thrown:
        #   total_runs = 115 and parallelism = 3
        #     does NOT cause maximum recursion depth exceeded on Dan's machine
        #
        #   Max Recursion error is thrown:
        #   total_runs = 200 and parallelism = 2
        #     causes maximum recursion depth exceeded on Dan's machine
        #
        # After the fix:
        #   total_runs = 200 and parallelism = 2
        #     no longer causes maximum recursion
        #
        # sleep = 10 was enough time on Dan's machine to make all cases work

        self.total_runs = 200
        self.parallelism = 2
        self.sleep = 10

        # crank up the queue parallel report configuration
        self.save_parallelism = queue.conf['MAX_PARALLEL_PER_RUN']
        self.save_instances = queue.conf['MAX_INSTANCES_PER_RECURRENT_REPORT']
        self.save_eager = queue.conf['CELERY_ALWAYS_EAGER']
        queue.conf['MAX_PARALLEL_PER_RUN'] = self.parallelism
        queue.conf['MAX_INSTANCES_PER_RECURRENT_REPORT'] = self.total_runs
        queue.conf['CELERY_ALWAYS_EAGER'] = False

    def tearDown(self):
        # re-enable the scheduler after these tests
        queue.conf['MAX_PARALLEL_PER_RUN'] = self.save_parallelism
        queue.conf['MAX_INSTANCES_PER_RECURRENT_REPORT'] = self.save_instances
        queue.conf['CELERY_ALWAYS_EAGER'] = self.save_eager
        DatabaseTest.tearDown(self)

    @attr('manual')
    def test_many_parallel_runs(self):
        parameters = {
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-01-01 00:00:00',
                'end_date': '2013-01-03 00:00:00',
                'individualResults': True,
                'aggregateResults': False,
                'aggregateSum': False,
                'aggregateAverage': False,
                'aggregateStandardDeviation': False,
            },
            'recurrent': True,
        }

        jr = RunReport(
            parameters,
            user_id=self.owner_user_id,
            created=datetime.today() - timedelta(days=self.total_runs)
        )
        jr.task.delay(jr).get()
        self.session.commit()

        # executing directly the code that will be run by the scheduler
        recurring_reports()

        time.sleep(self.sleep)

        recurrent_runs = self.session.query(ReportStore) \
            .filter(ReportStore.recurrent_parent_id == jr.persistent_id) \
            .all()

        successful_runs = filter(lambda x: x.status == 'SUCCESS', recurrent_runs)

        # make sure we have one and no more than one recurrent run
        assert_equal(len(successful_runs), self.total_runs)
