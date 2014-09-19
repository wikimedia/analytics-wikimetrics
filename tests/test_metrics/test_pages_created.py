from nose.tools import assert_true, assert_not_equal, assert_equal
from tests.fixtures import DatabaseTest

from wikimetrics.metrics import PagesCreated


class PagesCreatedTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_4()

    # Evan has 3 pages created, one in namespace 301, one in 302, and one in 303
    # (see tests/fixtures.py for details)
    # So here we just test if the number of pages created in those namespaces is
    # actually 3
    def test_case_basic(self):
        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-19 00:00:00',
            end_date='2013-08-21 00:00:00'
        )
        results = metric(self.editor_ids, self.mwSession)
        assert_equal(results[self.editors[0].user_id]["pages_created"], 3)
        assert_equal(results[self.editors[1].user_id]["pages_created"], 1)

    def test_case_uses_namespace_filter(self):
        metric = PagesCreated(
            namespaces=[0],
            start_date='2013-06-19 00:00:00',
            end_date='2013-08-21 00:00:00'
        )
        results = metric(self.editor_ids, self.mwSession)
        assert_equal(results[self.editors[0].user_id]["pages_created"], 0)
        assert_equal(results[self.editors[1].user_id]["pages_created"], 0)

    def test_case_no_namespace_includes_all(self):
        metric = PagesCreated(
            namespaces=[],
            start_date='2013-06-19 00:00:00',
            end_date='2013-08-21 00:00:00'
        )
        results = metric(self.editor_ids, self.mwSession)
        assert_equal(results[self.editors[0].user_id]["pages_created"], 3)
        assert_equal(results[self.editors[1].user_id]["pages_created"], 1)

    # same thing as before, but this time we leave one page created
    # out of the date range to see if date ranges work properly
    def test_case_uses_date_range(self):
        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-19 00:00:00',
            end_date='2013-07-21 00:00:00'
        )
        # TODO these tests need to go through cohort service,
        # cannot be using a storage object
        results = metric(self.editor_ids, self.mwSession)
        assert_equal(results[self.editors[0].user_id]["pages_created"], 2)

    def test_filters_out_other_editors(self):
        self.common_cohort_4(cohort=False)
        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-19 00:00:00',
            end_date='2013-08-21 00:00:00'
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(len(results), 2)

    def test_runs_for_an_entire_wiki(self):
        self.common_cohort_4(cohort=False)
        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-19 00:00:00',
            end_date='2013-08-21 00:00:00'
        )
        results = metric(None, self.mwSession)

        assert_equal(len(results), 4)
        assert_equal(results[self.editors[0].user_id]["pages_created"], 3)
        assert_equal(results[self.editors[1].user_id]["pages_created"], 1)
        # NOTE: this is a bit precarious as it assumes the order of test data inserts
        assert_equal(results[self.editors[0].user_id + 2]["pages_created"], 3)

    def test_case_basic_with_archive(self):
        self.archive_revisions()
        self.test_case_basic()

    def test_case_uses_namespace_filter_with_archive(self):
        self.archive_revisions()
        self.test_case_uses_namespace_filter()

    def test_case_no_namespace_includes_all_with_archive(self):
        self.archive_revisions()
        self.test_case_no_namespace_includes_all()

    def test_case_uses_date_range_with_archive(self):
        self.archive_revisions()
        self.test_case_uses_date_range()

    def test_filters_out_other_editors_with_archive(self):
        self.archive_revisions()
        self.test_filters_out_other_editors()

    def test_runs_for_an_entire_wiki_with_archive(self):
        self.archive_revisions()
        self.test_runs_for_an_entire_wiki()
