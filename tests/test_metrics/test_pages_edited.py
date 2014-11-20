from nose.tools import assert_true, assert_equal
from tests.fixtures import DatabaseTest

from wikimetrics.metrics import PagesEdited


class PagesEditedDatabaseTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_4()

    def test_filters_out_other_editors(self):
        self.common_cohort_1(cohort=False)
        metric = PagesEdited(
            start_date='2012-12-31 22:59:59',
            end_date='2014-01-01 00:00:00',
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(len(results), 2)
        assert_equal(results[self.editors[0].user_id][PagesEdited.id], 4)
        assert_equal(results[self.editors[1].user_id][PagesEdited.id], 2)

    def test_filters_out_other_editors_deduplicate(self):
        self.common_cohort_1(cohort=False)
        metric = PagesEdited(
            deduplicate_across_users=True,
            start_date='2012-12-31 22:59:59',
            end_date='2014-01-01 00:00:00',
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(len(results), 1)
        assert_equal(results[-1][PagesEdited.id], 5)

    def test_runs_for_an_entire_wiki(self):
        self.common_cohort_1(cohort=False)
        metric = PagesEdited(
            start_date='2012-12-31 22:59:59',
            end_date='2014-01-01 00:00:00',
        )
        results = metric(None, self.mwSession)

        assert_equal(len(results), 6)
        assert_equal(results[self.editors[0].user_id][PagesEdited.id], 4)
        assert_equal(results[self.editors[1].user_id][PagesEdited.id], 2)
        # NOTE: this is a bit precarious as it assumes the order of test data inserts
        assert_equal(results[self.editors[0].user_id + 4][PagesEdited.id], 1)

    def test_reports_zero_edits(self):
        metric = PagesEdited(
            namespaces=[0],
            start_date='2011-01-01 00:00:00',
            end_date='2011-02-01 00:00:00',
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_true(results is not None)
        assert_equal(results[self.editors[0].user_id][PagesEdited.id], 0)

    def test_filters_out_other_editors_with_archive(self):
        self.archive_revisions()
        self.test_filters_out_other_editors()

    def test_runs_for_an_entire_wiki_with_archive(self):
        self.archive_revisions()
        self.test_runs_for_an_entire_wiki()

    def test_reports_zero_edits_with_archive(self):
        self.archive_revisions()
        self.test_reports_zero_edits()
