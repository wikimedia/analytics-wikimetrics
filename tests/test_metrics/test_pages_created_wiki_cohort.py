from nose.tools import assert_equal

from tests.fixtures import DatabaseTest
from wikimetrics.metrics import PagesCreated
from wikimetrics.api import CohortService


class PagesCreatedWikiCohortTest(DatabaseTest):
    def setUp(self):
        """
        Setup editing data using a regular cohort setup
        Setup a WikiCohort that will span to all users that we have
        in the project.

        """
        DatabaseTest.setUp(self)
        self.common_cohort_4()
        self.create_wiki_cohort()
        self.cohort_service = CohortService()
        self.wiki_cohort = self.cohort_service.get(
            self.session, self.owner_user_id, by_id=self.basic_wiki_cohort.id
        )
        # This should return an empty list, but if it returned anything, the objects
        # would be WikiUserStore objects, so we should treat it as such
        self.user_ids = [
            w.mediawiki_userid
            for w in self.cohort_service.get_wikiusers(self.wiki_cohort, self.session)
        ]

    def test_pages_created_happy_case(self):
        """
        Retrieve pages created metric for wiki cohort for project 'wiki'
        Results of tests should be identical as if we used cohort number 4
        """
        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-19 00:00:00',
            end_date='2013-08-21 00:00:00'
        )
        results = metric(self.user_ids, self.mwSession)

        assert_equal(results[self.editors[0].user_id]['pages_created'], 3)
        assert_equal(results[self.editors[1].user_id]['pages_created'], 1)

    def test_pages_created_extra_users(self):
        """
        Retrieve pages created metric for wiki cohort for project 'wiki'
        Results should include the additional users created by
        `self.common_cohort_4(cohort=False)`
        """
        self.common_cohort_4(cohort=False)

        metric = PagesCreated(
            namespaces=[301, 302, 303],
            start_date='2013-06-19 00:00:00',
            end_date='2013-08-21 00:00:00'
        )
        results = metric(self.user_ids, self.mwSession)

        assert_equal(results[self.editors[0].user_id]['pages_created'], 3)
        assert_equal(results[self.editors[1].user_id]['pages_created'], 1)
        assert_equal(results[self.editors[0].user_id + 2]['pages_created'], 3)
        assert_equal(results[self.editors[1].user_id + 2]['pages_created'], 1)
