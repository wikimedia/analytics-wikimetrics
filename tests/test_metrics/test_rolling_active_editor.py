from datetime import datetime, timedelta
from nose.tools import assert_true, assert_equal, assert_false

from tests.fixtures import DatabaseTest, i, d
from wikimetrics.utils import format_pretty_date as s
from wikimetrics.models import Revision, MediawikiUser
from wikimetrics.metrics import RollingActiveEditor
from wikimetrics.enums import TimeseriesChoices


class RollingActiveEditorTest(DatabaseTest):
    """
        TODO: add timeseries support and use the following tests:
        gerrit.wikimedia.org/r/#/c/147312/5/tests/test_metrics/test_rolling_active_editor.py
    """
    def runTest(self):
        pass

    def setUp(self):
        DatabaseTest.setUp(self)

        # registration for all the editors below
        self.r = r = 20140101000000
        # exactly 30 days after registration
        self.m = m = 20140131000000
        self.r_plus_30 = s(d(self.m))

        self.create_test_cohort(
            editor_count=5,
            revisions_per_editor=8,
            revision_timestamps=[
                # this one will make 5 edits within 30 days of self.r_plus_30
                [r + 1, r + 2, r + 3, r + 4, r + 5, m + 6, m + 7, m + 8],
                # this one will make 3 edits within 30 days of self.r_plus_30
                [r + 1, r + 2, r + 3, m + 4, m + 5, m + 6, m + 7, m + 8],
                # this one will make 8 edits within 30 days of self.r_plus_30
                [r + 1, r + 2, r + 3, r + 4, r + 5, r + 6, r + 7, r + 8],
                # this one will make 0 edits within 30 days of self.r_plus_30
                [m + 1, m + 2, m + 3, m + 4, m + 5, m + 6, m + 7, m + 8],
                # this one will make the 5th edit right on self.r_plus_30
                [r + 1, r + 2, r + 3, r + 4, m + 0, m + 6, m + 7, m + 8],
            ],
            user_registrations=r,
            revision_lengths=10
        )
        self.create_non_editors([
            (r, 'newusers', 'create'),
            (r, 'newusers', 'create'),
            (m, 'newusers', 'create'),
        ])

    def test_validates(self):
        metric = RollingActiveEditor(
            end_date='blah'
        )
        assert_false(metric.validate())

        metric = RollingActiveEditor(
            end_date=self.r_plus_30,
        )
        assert_true(metric.validate())

    def test_normal_cohort(self):
        metric = RollingActiveEditor(
            end_date=self.r_plus_30,
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(set(results.keys()), set(self.editor_ids))
        assert_equal([1, 0, 1, 0, 1], [
            results[self.editor_ids[x]][metric.id] for x in range(5)
        ])

    def test_normal_cohort_with_archived_revisions(self):
        self.archive_revisions()
        self.test_normal_cohort()

    def test_wiki_cohort(self):
        # make one of the non-cohort users, who registered on self.r, active
        make_active = self.non_editors[0]
        self.mwSession.bind.engine.execute(
            Revision.__table__.insert(), [
                {
                    'rev_page'      : self.page.page_id,
                    'rev_user'      : make_active.user_id,
                    'rev_comment'   : 'revision {}, additional'.format(rev),
                    'rev_timestamp' : self.r + rev,
                    'rev_len'       : 10,
                    # rev_parent_id will not be set
                }
                for rev in range(1, 6)
            ]
        )
        self.mwSession.commit()

        expected = set(self.editor_ids + [make_active.user_id])
        # editors with no edits at all won't be picked up by the query
        expected.remove(self.editor_ids[3])
        # editors that haven't made enough queries won't pass the test
        expected.remove(self.editor_ids[1])

        metric = RollingActiveEditor(
            end_date=self.r_plus_30,
        )
        results = metric(None, self.mwSession)

        # all wiki cohort results will be editors that pass the test
        assert_equal(set(results.keys()), expected)
        for user_id in expected:
            assert_equal(results[user_id][metric.id], 1)

    def test_wiki_cohort_all_bots(self):
        # make everyone a bot and make sure they're excluded
        for r in self.mwSession.query(MediawikiUser.user_id).all():
            self.make_bot(r[0], self.mwSession)

        metric = RollingActiveEditor(
            end_date=self.r_plus_30,
        )
        results = metric(None, self.mwSession)

        assert_equal(results.keys(), [])
