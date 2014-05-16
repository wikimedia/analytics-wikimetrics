from datetime import datetime
from nose.tools import assert_true, assert_equal, nottest
from tests.fixtures import QueueDatabaseTest, DatabaseTest
from wikimetrics.metrics import RevertRate, TimeseriesChoices


class RevertRateTest(DatabaseTest):

    def setUp(self):
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=2,
            revisions_per_editor=3,
            revision_timestamps=[
                [20121231230000, 20130101003000, 20130101010000],
                [20130101120000, 20130102000000, 20130102120000],
            ],
            revision_lengths=[
                [1, 2, 3],  # User A makes some edits.
                [2, 4, 5],  # User B reverts user A's edit #3 back to edit #2.
            ],
        )

    @nottest
    def test_single_revert(self):
        metric = RevertRate(
            # namespaces=[0],
            start_date='2012-12-31 00:00:00',
            end_date='2014-01-02 00:00:00',
            timeseries=TimeseriesChoices.DAY,
        )
        results = metric(list(self.cohort), self.mwSession)

        results_should_be = {
            # User A had one revert
            self.editors[0].user_id: {
                'edits': 3,
                'reverts': 1,
                'revert_rate': float(1) / float(3),
            },
            # User B had no reverts
            self.editors[1].user_id: {
                'edits': 3,
                'reverts': 0,
                'revert_rate': 0,
            },
        }

        # check user A's results
        assert_equal(
            results[self.editors[0].user_id],
            results_should_be[self.editors[0].user_id]
        )

        # check user B's results
        assert_equal(
            results[self.editors[1].user_id],
            results_should_be[self.editors[0].user_id]
        )
