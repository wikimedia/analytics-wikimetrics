from datetime import datetime, timedelta
from nose.tools import assert_true, assert_equal, assert_false

from tests.fixtures import DatabaseTest, i
from wikimetrics.metrics import NewlyRegistered


class NewlyRegisteredTest(DatabaseTest):
    def runTest(self):
        pass

    def setUp(self):
        DatabaseTest.setUp(self)

        one_hour = timedelta(hours=1)
        first_reg = datetime.now() - one_hour * 100

        self.create_test_cohort(
            editor_count=3,
            revisions_per_editor=2,
            revision_timestamps=i(first_reg + one_hour * 100),
            user_registrations=[
                i(first_reg),
                i(first_reg + one_hour * 20),
                i(first_reg + one_hour * 30),
            ],
            revision_lengths=10
        )
        self.create_non_editors([
            (first_reg + one_hour       , 'proxy'   , 'proxy'),
            (first_reg + one_hour       , 'proxy'   , 'attached'),
            (first_reg + one_hour       , 'proxy'   , 'create'),
            (first_reg + one_hour       , 'newusers', 'proxy'),
            (first_reg + one_hour       , 'newusers', 'attached'),
            (first_reg + one_hour       , 'newusers', 'create'),
            (first_reg - one_hour * 1000, 'newusers', 'proxy'),
            (first_reg - one_hour * 1000, 'proxy'   , 'proxy'),
            (first_reg - one_hour * 1000, 'proxy'   , 'create'),
            (first_reg - one_hour * 1000, 'newusers', 'create'),
        ])
        # these are useful to set up the tests
        self.first_reg = first_reg
        self.one_hour = one_hour

    def test_filters_out_other_users(self):
        metric = NewlyRegistered(
            start_date=self.first_reg,
            end_date=self.first_reg + self.one_hour * 21,
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(set(results.keys()), set(self.editor_ids))

    def test_runs_for_an_entire_wiki(self):
        metric = NewlyRegistered(
            start_date=self.first_reg,
            end_date=self.first_reg + self.one_hour * 21,
        )
        results = metric(None, self.mwSession)

        assert_equal(len(results), 2)
        assert_equal(results[self.editors[1].user_id][metric.id], 1)
        assert_true(self.editors[0] not in results)
        assert_true(self.editors[2] not in results)

    def test_correct_result(self):
        metric = NewlyRegistered(
            start_date=self.first_reg,
            end_date=self.first_reg + self.one_hour * 21,
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(results[self.editors[0].user_id][metric.id], 0)
        assert_equal(results[self.editors[1].user_id][metric.id], 1)
        assert_equal(results[self.editors[2].user_id][metric.id], 0)

    def test_validates(self):
        metric = NewlyRegistered(
            start_date='blah'
        )
        assert_false(metric.validate())

        metric = NewlyRegistered(
            start_date=self.first_reg,
            end_date=self.first_reg + self.one_hour * 21,
        )
        assert_true(metric.validate())
