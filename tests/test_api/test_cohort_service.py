from nose.tools import assert_equals, assert_true, raises
from sqlalchemy.orm.exc import NoResultFound

from tests.fixtures import DatabaseTest
from wikimetrics.api import CohortService
from wikimetrics.exceptions import Unauthorized, InvalidCohort
from wikimetrics.models import CohortStore, CohortUserStore, CohortUserRole


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
        users = self.cohort_service.get_wikiusers(self.fixed_cohort)
        assert_equals(users, self.editor_user_ids)

    def test_get_wikiusers_limited(self):
        users = self.cohort_service.get_wikiusers(self.fixed_cohort, 2)
        assert_equals(len(users), 2)

    def test_get_wikiusers_empty(self):
        users = self.cohort_service.get_wikiusers(self.empty_cohort)
        assert_equals(len(users), 0)
