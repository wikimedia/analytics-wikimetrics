from datetime import datetime, timedelta
from nose.tools import assert_true, assert_equal, assert_false

from tests.fixtures import DatabaseTest, i, d
from wikimetrics.utils import format_pretty_date as s
from wikimetrics.models import Revision, Logging, MediawikiUser
from wikimetrics.metrics import RollingSurvivingNewActiveEditor
from wikimetrics.enums import TimeseriesChoices


class RollingSurvivingNewActiveEditorTest(DatabaseTest):
    """
        TODO: add timeseries support and use the following tests:
        gerrit.wikimedia.org/r/#/c/147312/5/tests/test_metrics/test_rolling_active_editor.py
    """
    def runTest(self):
        pass

    def setUp(self):
        DatabaseTest.setUp(self)

        # registration for all the editors below
        self.before_r = before_r = 20131201000000
        self.r = r = 20140101000000
        # exactly 30 days after registration
        self.m = m = 20140131000000
        # exactly 60 days after registration
        self.m2 = m2 = 20140302000000
        self.r_plus_60 = s(d(self.m2))
        self.editor_count = 14

        self.create_test_cohort(
            # 5 editors will have registered on time, 5 will not
            editor_count=self.editor_count,
            revisions_per_editor=10,
            revision_timestamps=[
                # NOTE: these first 6 are registered BEFORE r
                # this one will make 7 edits within 30 days of m, 3 after
                [r] * 7 + [m + 1] * 3,
                # this one will make 3 edits within 30 days of m, 7 after
                [r] * 3 + [m + 1] * 7,
                # this one will make 10 edits within 30 days of m, 0 after
                [r] * 10,
                # this one will make 0 edits within 30 days of m, 10 after
                [m + 1] * 10,
                # this one will make 5 edits within 30 days of m, 5 after
                [r] * 5 + [m + 1] * 5,
                # this one will make the 5th edit right on m, 5 after
                [r] * 4 + [m] + [m + 1] * 5,
                # this one will make no edits within r -> r + 60 days
                [m2 + 1] * 10,

                # NOTE: these next 6 are registered AFTER r
                # this one will make 7 edits within 30 days of m, 3 after
                [r] * 7 + [m + 1] * 3,
                # this one will make 3 edits within 30 days of m, 7 after
                [r] * 3 + [m + 1] * 7,
                # this one will make 10 edits within 30 days of m, 0 after
                [r] * 10,
                # this one will make 0 edits within 30 days of m, 10 after
                [m + 1] * 10,
                # this one will make 5 edits within 30 days of m, 5 after
                [r] * 5 + [m + 1] * 5,
                # this one will make the 5th edit right on m, 5 after
                [r] * 4 + [m] + [m + 1] * 5,
                # this one will make no edits within r -> r + 60 days
                [m2 + 1] * 10,
            ],
            user_registrations=([before_r] * 7) + ([r] * 7),
            revision_lengths=10
        )
        self.create_non_editors([
            (r, 'newusers', 'create'),
            (r, 'newusers', 'create'),
            (m, 'newusers', 'create'),
        ])

    def test_validates(self):
        metric = RollingSurvivingNewActiveEditor(
            end_date='blah'
        )
        assert_false(metric.validate())

        metric = RollingSurvivingNewActiveEditor(
            end_date=self.r_plus_60,
        )
        assert_true(metric.validate())

    def test_normal_cohort(self):
        metric = RollingSurvivingNewActiveEditor(
            end_date=self.r_plus_60,
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(set(results.keys()), set(self.editor_ids))
        assert_equal([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0], [
            results[self.editor_ids[x]][metric.id] for x in range(self.editor_count)
        ])

    def test_normal_cohort_with_archived_revisions(self):
        self.archive_revisions()
        self.test_normal_cohort()

    def test_wiki_cohort(self):
        # make one of the non-cohort users, who registered on self.r, recurring active
        # NOTE: need to add two sets of 5 edits to make "recurring" active
        make_active = self.non_editors[0]
        for timestamp in [self.r, self.m]:
            self.mwSession.bind.engine.execute(
                Revision.__table__.insert(), [
                    {
                        'rev_page'      : self.page.page_id,
                        'rev_user'      : make_active.user_id,
                        'rev_comment'   : 'revision {}, additional'.format(rev),
                        'rev_timestamp' : timestamp + rev,
                        'rev_len'       : 10,
                        # rev_parent_id will not be set
                    }
                    for rev in range(1, 6)
                ]
            )
        self.mwSession.commit()

        expected = set(self.editor_ids + [make_active.user_id])
        # editors with no edits at all won't be picked up by the query
        expected.remove(self.editor_ids[13])
        # editors that haven't registered in time shouldn't be picked up at all
        for reg_before in range(7):
            expected.remove(self.editor_ids[reg_before])

        metric = RollingSurvivingNewActiveEditor(
            end_date=self.r_plus_60,
        )
        results = metric(None, self.mwSession)

        assert_equal(set(results.keys()), expected)
        expected_results = {
            # all actives show, whether in a cohort or not
            self.editor_ids[11] : 1,
            self.editor_ids[12] : 1,
            make_active.user_id : 1,
            # users with not enough edits will show up with 0 as the result
            self.editor_ids[7] : 0,
            self.editor_ids[8] : 0,
            self.editor_ids[9] : 0,
            self.editor_ids[10] : 0,
        }
        print expected_results
        print results
        for user_id, result in expected_results.items():
            assert_equal(results[user_id][metric.id], result)

    def test_wiki_cohort_nobody_qualifying(self):
        # make everyone fail the registration criteria and make sure they're excluded
        self.mwSession.bind.engine.execute(
            Logging.__table__.update().values({
                'log_type': 'blah'
            })
        )
        self.mwSession.commit()

        metric = RollingSurvivingNewActiveEditor(
            end_date=self.r_plus_60,
        )
        results = metric(None, self.mwSession)

        assert_equal(results.keys(), [])

    def test_wiki_cohort_all_bots(self):
        # make everyone a bot and make sure they're excluded
        for r in self.mwSession.query(MediawikiUser.user_id).all():
            self.make_bot(r[0], self.mwSession)

        metric = RollingSurvivingNewActiveEditor(
            end_date=self.r_plus_60,
        )
        results = metric(None, self.mwSession)

        assert_equal(results.keys(), [])
