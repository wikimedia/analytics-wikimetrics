from nose.tools import assert_equals, assert_true, raises
from sqlalchemy.orm.exc import NoResultFound

from tests.fixtures import DatabaseTest, mediawiki_project
from wikimetrics.api import CohortService
from wikimetrics.exceptions import Unauthorized, InvalidCohort
from wikimetrics.models import CohortStore, CohortUserStore
from wikimetrics.enums import CohortUserRole
from wikimetrics.models.cohorts import Cohort


class CohortServiceTest(DatabaseTest):

    def setUp(self):
        """
        NOTE: self.cohort is a CohortStore object.  When testing CohortService,
        one should use logical cohort objects (ie. FixedCohort, WikiCohort, etc.)
        """
        DatabaseTest.setUp(self)
        self.common_cohort_1()
        self.editor_user_ids = [e.user_id for e in self.editors]
        self.cohort_service = CohortService()

        empty_cohort = CohortStore(enabled=True, class_name='Cohort')
        self.session.add(empty_cohort)
        self.session.commit()
        empty_cohort_user = CohortUserStore(
            user_id=self.owner_user_id,
            cohort_id=empty_cohort.id,
            role=CohortUserRole.OWNER,
        )
        self.session.add(empty_cohort_user)
        self.session.commit()

        self.invalid_empty_cohort = CohortStore(
            enabled=True, class_name='FixedCohort', validated=True
        )
        self.session.add(self.invalid_empty_cohort)
        self.session.commit()
        invalid_empty_cohort_user = CohortUserStore(
            user_id=self.owner_user_id,
            cohort_id=self.invalid_empty_cohort.id,
            role=CohortUserRole.OWNER,
        )
        self.session.add(invalid_empty_cohort_user)
        self.session.commit()

        self.empty_cohort = self.cohort_service.get(
            self.session, self.owner_user_id, by_id=empty_cohort.id
        )
        self.fixed_cohort = self.cohort_service.get(
            self.session, self.owner_user_id, by_id=self.cohort.id
        )

    def test_get(self):
        assert_equals(self.fixed_cohort.name, self.cohort.name)

    def test_get_by_name(self):
        c = self.cohort_service.get(
            self.session, self.owner_user_id, by_name=self.cohort.name
        )
        assert_equals(c.name, self.cohort.name)

    def test_get_empty(self):
        assert_equals(self.empty_cohort.name, None)

    @raises(NoResultFound)
    def test_get_raises_exception_for_not_found_by_id(self):
        self.cohort_service.get(self.session, self.owner_user_id, by_id=0)

    @raises(NoResultFound)
    def test_get_raises_exception_for_not_found_by_name(self):
        self.cohort_service.get(self.session, self.owner_user_id, by_name='')

    @raises(Unauthorized)
    def test_get_unauthorized(self):
        self.cohort_service.get(self.session, 0, by_id=self.cohort.id)

    @raises(InvalidCohort)
    def test_get_invalid(self):
        self.cohort.validated = False
        self.session.commit()
        self.cohort_service.get(self.session, self.owner_user_id, by_id=self.cohort.id)

    @raises(InvalidCohort)
    def test_get_invalid_because_empty(self):
        self.cohort_service.get(
            self.session, self.owner_user_id, by_id=self.invalid_empty_cohort.id
        )

    def test_get_size(self):
        assert_equals(self.fixed_cohort.size, 4)

    def test_get_size_empty(self):
        assert_equals(self.empty_cohort.size, 0)

    def test_get_users_by_project(self):
        c = self.cohort_service.get(
            self.session, self.owner_user_id, by_id=self.cohort.id
        )
        by_project = self.cohort_service.get_users_by_project(c)

        # NOTE: generator magic, couldn't get this to work without a loop
        for p in by_project:
            wikiusers = list(p[1])
            assert_equals(set(self.editor_user_ids), set(wikiusers))

        assert_equals(len(wikiusers), 4)

    def test_get_wikiusers(self):
        users = self.cohort_service.get_wikiusers(self.fixed_cohort, self.session)
        assert_equals(users, self.editor_user_ids)

    def test_get_wikiusers_limited(self):
        users = self.cohort_service.get_wikiusers(self.fixed_cohort, self.session, 2)
        assert_equals(len(users), 2)

    def test_get_wikiusers_empty(self):
        users = self.cohort_service.get_wikiusers(self.empty_cohort, self.session)
        assert_equals(len(users), 0)

    def test_wiki_cohort_group_by_project_works(self):
        self.create_wiki_cohort()
        c = self.cohort_service.get(
            self.session, self.owner_user_id, by_id=self.basic_wiki_cohort.id
        )
        users_by_project = list(self.cohort_service.get_users_by_project(c))
        assert_equals(len(users_by_project), 1)
        assert_equals(users_by_project[0][0], mediawiki_project)
        assert_equals(users_by_project[0][1], None)

    def test_convert(self):
        cohort = self.cohort_service.convert(self.cohort)
        assert_true(issubclass(cohort.__class__, Cohort))

    def test_add_wiki_cohort(self):
        dewiki1 = self.cohort_service.add_wiki_cohort(self.session, 'dewiki')
        assert_equals(dewiki1.name, 'dewiki')
        assert_equals(dewiki1.default_project, 'dewiki')
        assert_equals(type(dewiki1).__name__, 'WikiCohort')
        assert_equals(dewiki1.enabled, True)
        dewiki2 = self.cohort_service.add_wiki_cohort(self.session, 'dewiki')
        # make sure the cohort doesn't get added twice
        assert_equals(dewiki1.id, dewiki2.id)

    def test_share(self):
        cohorts = self.cohort_service.get_list(self.session, self.owner_user_id)
        assert_true('dewiki' not in [c.default_project for c in cohorts])

        dewiki = self.cohort_service.add_wiki_cohort(self.session, 'dewiki')
        self.cohort_service.share(self.session, dewiki, self.owner_user_id)

        cohorts = self.cohort_service.get_list(self.session, self.owner_user_id)
        assert_true('dewiki' in [c.default_project for c in cohorts])

    def test_wikiusernames_for_not_existing_cohort(self):
        """
        If a cohort does not exist it returns an empty list of user names to make
        things easy for the UI
        """
        user_names = self.cohort_service.get_wikiusernames_for_cohort('9999',
                                                                      self.session)
        assert_equals(len(user_names.keys()), 0)

    def test_wikiusernames(self):
        """
        Make sure usernames can be retrieved using Wikiuserkey
        """
        from wikimetrics.models.storage import (
            WikiUserKey
        )
        # let's get two users and see that names match
        # this returns a list of WikiUserStore objects
        users = self.cohort_service.get_wikiusers(self.fixed_cohort, self.session, 2)
        user1 = users[0]
        key1 = WikiUserKey(user1.mediawiki_userid, user1.project,
                           user1.validating_cohort)

        user2 = users[1]
        key2 = WikiUserKey(user2.mediawiki_userid, user2.project,
                           user2.validating_cohort)

        user_names = self.cohort_service.get_wikiusernames_for_cohort(
            self.fixed_cohort.id, self.session)

        assert_equals(user_names[key1], user1.mediawiki_username)
        assert_equals(user_names[key2], user2.mediawiki_username)
