# -*- coding: utf-8 -*-
from nose.tools import assert_equals, assert_true, assert_false, raises
from sqlalchemy.orm.exc import NoResultFound

from tests.fixtures import DatabaseTest, mediawiki_project
from wikimetrics.api import CohortService
from wikimetrics.exceptions import Unauthorized, InvalidCohort
from wikimetrics.models import (
    CohortStore, CohortUserStore, WikiUserStore, CohortWikiUserStore,
    CohortTagStore, TagStore
)
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

    def test_get_membership_contents(self):
        """
        The wikiuser properties must be returned
        under the expected data structure.
        """
        wikiusers = self.session.query(WikiUserStore).all()
        membership = self.cohort_service.get_membership(self.cohort, self.session)

        assert_equals(len(membership), len(wikiusers))
        for i in range(len(membership)):
            wikiuser, member = wikiusers[i], membership[i]
            assert_equals(len(membership), 4)
            assert_equals(member['username'], wikiuser.mediawiki_username)
            assert_equals(len(member['projects']), 1)
            assert_equals(member['projects'][0], wikiuser.project)
            assert_equals(len(member['invalidProjects']), 0)
            assert_equals(len(member['invalidReasons']), 0)

    def test_get_membership_group_by_username(self):
        """
        The wikiusers must be grouped by username,
        returning their projects, validities and reasons
        in the corresponding lists.
        """
        wikiusers = self.session.query(WikiUserStore).all()
        username_1, username_2 = 'Username 1', 'Username 2'
        project_1, project_2 = 'Project 1', 'Project 2'
        reason_invalid_1 = 'Reason Invalid 1'

        wikiusers[0].mediawiki_username = username_1
        wikiusers[1].mediawiki_username = username_1
        wikiusers[2].mediawiki_username = username_2
        wikiusers[2].project = project_1
        wikiusers[3].mediawiki_username = username_2
        wikiusers[3].project = project_2
        wikiusers[3].valid = False
        wikiusers[3].reason_invalid = reason_invalid_1
        self.session.commit()

        membership = self.cohort_service.get_membership(self.cohort, self.session)

        assert_equals(len(membership), 2)
        assert_equals(membership[0]['username'], username_1)
        assert_equals(membership[1]['username'], username_2)
        assert_equals(membership[1]['projects'], [project_1, project_2])
        assert_equals(membership[1]['invalidProjects'], [project_2])
        assert_equals(membership[1]['invalidReasons'], [reason_invalid_1])

    def test_get_membership_order_by_name(self):
        wikiusers = self.session.query(WikiUserStore).all()
        wikiusers[0].mediawiki_username = 'D'
        wikiusers[1].mediawiki_username = 'C'
        wikiusers[2].mediawiki_username = 'B'
        wikiusers[3].mediawiki_username = 'A'
        self.session.commit()

        membership = self.cohort_service.get_membership(self.cohort, self.session)
        assert_equals(len(membership), len(wikiusers))
        assert_equals(membership[0]['username'], 'A')
        assert_equals(membership[1]['username'], 'B')
        assert_equals(membership[2]['username'], 'C')
        assert_equals(membership[3]['username'], 'D')

    def test_delete_cohort_wikiuser(self):
        username = 'To Delete'
        wikiuser = self.session.query(WikiUserStore).first()
        wikiuser.mediawiki_username = username
        self.session.commit()

        self.cohort_service.delete_cohort_wikiuser(
            username, self.cohort.id, self.owner_user_id, self.session)

        wikiusers = (
            self.session.query(WikiUserStore)
            .filter(WikiUserStore.mediawiki_username == username)
            .filter(WikiUserStore.validating_cohort == self.cohort.id)
            .all())
        assert_equals(len(wikiusers), 0)
        cohort_wikiusers = (
            self.session.query(CohortWikiUserStore)
            .filter(CohortWikiUserStore.cohort_id == self.cohort.id)
            .filter(CohortWikiUserStore.wiki_user_id == wikiuser.id)
            .all())
        assert_equals(len(cohort_wikiusers), 0)

    def test_delete_cohort_wikiuser_invalid_only(self):
        username = 'To Delete'
        wikiusers = self.session.query(WikiUserStore).all()
        wikiusers[0].mediawiki_username = username
        wikiusers[1].mediawiki_username = username
        wikiusers[1].valid = False
        wikiuser_ids = [wikiusers[0].id, wikiusers[1]]
        self.session.commit()

        self.cohort_service.delete_cohort_wikiuser(
            username, self.cohort.id, self.owner_user_id, self.session, True)

        wikiusers = (
            self.session.query(WikiUserStore)
            .filter(WikiUserStore.mediawiki_username == username)
            .filter(WikiUserStore.validating_cohort == self.cohort.id)
            .all())
        assert_equals(len(wikiusers), 1)
        cohort_wikiusers = (
            self.session.query(CohortWikiUserStore)
            .filter(CohortWikiUserStore.cohort_id == self.cohort.id)
            .filter(CohortWikiUserStore.wiki_user_id.in_(wikiuser_ids))
            .all())
        assert_equals(len(cohort_wikiusers), 1)

    def test_delete_cohort_wikiuser_utf8(self):
        username = '18Наталь'
        wikiuser = self.session.query(WikiUserStore).first()
        wikiuser.mediawiki_username = username
        self.session.commit()

        self.cohort_service.delete_cohort_wikiuser(
            username, self.cohort.id, self.owner_user_id, self.session)

        wikiusers = (
            self.session.query(WikiUserStore)
            .filter(WikiUserStore.mediawiki_username == username)
            .filter(WikiUserStore.validating_cohort == self.cohort.id)
            .all())
        assert_equals(len(wikiusers), 0)

    @raises(Unauthorized)
    def test_delete_cohort_wikiuser_ownership(self):
        self.cohort_service.delete_cohort_wikiuser(
            'To Delete', self.cohort.id, self.owner_user_id + 1, self.session)

    def test_is_owned_by_user_positive(self):
        cohort_user = (
            self.session.query(CohortUserStore)
            .filter(CohortUserStore.cohort_id == self.cohort.id)
            .one())
        result = self.cohort_service.is_owned_by_user(
            self.session, self.cohort.id, cohort_user.user_id)
        assert_true(result)

    def test_is_owned_by_user_negative(self):
        cohort_user = (
            self.session.query(CohortUserStore)
            .filter(CohortUserStore.cohort_id == self.cohort.id)
            .one())
        result = self.cohort_service.is_owned_by_user(
            self.session, self.cohort.id, cohort_user.user_id + 1)
        assert_false(result)

    @raises(Unauthorized)
    def test_is_owned_by_user_exception(self):
        cohort_user = (
            self.session.query(CohortUserStore)
            .filter(CohortUserStore.cohort_id == self.cohort.id)
            .one())
        self.cohort_service.is_owned_by_user(
            self.session, self.cohort.id, cohort_user.user_id + 1, True)

    @raises(Unauthorized)
    def test_get_tag_exception(self):
        tag = TagStore(name='some_tag')
        self.session.add(tag)
        self.session.commit()

        cohort_tag = CohortTagStore(
            tag_id=tag.id,
            cohort_id=self.empty_cohort.id,
        )
        self.session.add(cohort_tag)
        self.session.commit()

        cohort_user = (
            self.session.query(CohortUserStore)
            .filter(CohortUserStore.cohort_id == self.empty_cohort.id)
            .one())

        self.cohort_service.get_tag(self.session, tag, self.empty_cohort.id,
                                    cohort_user.user_id + 1)

    def test_get_tag(self):
        tag = TagStore(name='some_tag')
        self.session.add(tag)
        self.session.commit()

        cohort_tag = CohortTagStore(
            tag_id=tag.id,
            cohort_id=self.empty_cohort.id,
        )
        self.session.add(cohort_tag)
        self.session.commit()

        cohort_user = (
            self.session.query(CohortUserStore)
            .filter(CohortUserStore.cohort_id == self.empty_cohort.id)
            .one())
        cohort_tags = self.cohort_service.get_tag(
            self.session, tag, self.empty_cohort.id, cohort_user.user_id)

        assert_equals(len(cohort_tags), 1)

    @raises(Unauthorized)
    def test_add_tag_exception(self):
        tag = TagStore(name='some_tag')
        self.session.add(tag)
        self.session.commit()

        cohort_user = (
            self.session.query(CohortUserStore)
            .filter(CohortUserStore.cohort_id == self.empty_cohort.id)
            .one())
        self.cohort_service.add_tag(self.session, tag, self.empty_cohort.id,
                                    cohort_user.user_id + 1)

    def test_add_tag(self):
        tag = TagStore(name='some_tag')
        self.session.add(tag)
        self.session.commit()

        cohort_user = (
            self.session.query(CohortUserStore)
            .filter(CohortUserStore.cohort_id == self.empty_cohort.id)
            .one())

        cohort_tags = self.cohort_service.get_tag(
            self.session, tag, self.empty_cohort.id, cohort_user.user_id)
        assert_equals(len(cohort_tags), 0)

        self.cohort_service.add_tag(
            self.session, tag, self.empty_cohort.id, cohort_user.user_id)
        cohort_tags = self.cohort_service.get_tag(
            self.session, tag, self.empty_cohort.id, cohort_user.user_id)

        assert_equals(len(cohort_tags), 1)
