from sqlalchemy.orm.exc import NoResultFound

from wikimetrics.configurables import db
from wikimetrics.exceptions import Unauthorized, InvalidCohort
from wikimetrics.models import cohort_classes, ValidatedCohort, WikiCohort
from wikimetrics.models.storage import (
    CohortStore, CohortUserStore, UserStore, CohortUserRole, WikiUserStore,
)


class CohortService(object):
    """
    General service that helps manage cohorts.  This is the bridge between:
        * plain data objects (instances of the models.cohorts.Cohort class hierarchy)
        * CohortStorage which is the way we persist cohorts to the database
    """

    def convert(self, cohort):
        """
        Converts a CohortStore object into a logical Cohort object
        """
        return cohort_classes[cohort.class_name](cohort, len(cohort))

    # TODO: check ownership of the cohort
    # TODO: once we have logical models for wikiusers, we may want to eagerly
    #       load wikiusers with the logical cohort instance and use that here
    def get_wikiusers(self, cohort, limit=None):
        """
        Parameters
            cohort: a logical Cohort object
            TODO: check ownership of the cohort

        Returns
            A list of WikiUser(s) that belong to this cohort or empty
            list if cohort spans the whole project. If cohort is None
            it also returns empty list
        """
        c = self.fetch(cohort)
        if limit:
            try:
                session = db.get_session()
                return c.filter_wikiuser_query(
                    session.query(WikiUserStore)).limit(limit).all()
            finally:
                session.close()
        else:
            return list(c)

    # TODO: check ownership of the cohort
    def get_users_by_project(self, cohort):
        """
        Parameters
            cohort  : a logical Cohort object

        Returns
            output of the form:
            (('project', (generator of user_ids)))
        """
        if cohort is None:
            return None

        c = self.fetch(cohort)
        return c.group_by_project()

    # TODO: check ownership of the cohort
    def fetch(self, cohort):
        """
        Fetches a CohortStore object from the database, without checking permissions

        Parameters
            cohort  : a logical Cohort object
        """
        db_session = db.get_session()
        return db_session.query(CohortStore).get(cohort.id)

    def get(self, db_session, user_id, **kargs):
        """Same as _get but checks validity of the cohort"""
        cohort = self._get(db_session, user_id, **kargs)
        if self.is_invalid(cohort) is True:
            raise InvalidCohort('This cohort is not valid')
        return cohort

    def get_for_display(self, db_session, user_id, **kargs):
        """Same as _get, also ignores validity of the cohort"""
        return self._get(db_session, user_id, **kargs)

    def _get(self, db_session, user_id, by_id=None, by_name=None):
        """
        Gets a Cohort but first checks permissions on it.

        Parameters
            db_session  : the database session to query
            user_id     : the user that should have access to the cohort
            by_id       : the cohort id to get.  <by_id> or <by_name> is True
            by_name     : the cohort name to get.  <by_id> or <by_name> is True

        Returns
            If found, an appropriate data object instance from models.cohorts

        Raises
            Unauthorized    : user_id is not allowed to access this cohort
        """
        query = db_session.query(CohortStore, CohortUserStore.role)\
            .join(CohortUserStore)\
            .join(UserStore)\
            .filter(UserStore.id == user_id)\
            .filter(CohortStore.enabled)

        if by_id is not None:
            f = lambda q: q.filter(CohortStore.id == by_id)
        if by_name is not None:
            f = lambda q: q.filter(CohortStore.name == by_name)

        try:
            cohort, role = f(query).one()
        except NoResultFound:
            cohort = f(db_session.query(CohortStore)).one()
            # if we get here it means there's a cohort,
            # but this user is not authorized to use it
            raise Unauthorized('You are not allowed to use this cohort')

        if role in CohortUserRole.SAFE_ROLES:
            return self.convert(cohort)
        else:
            raise Unauthorized('You are not allowed to use this cohort')

    def get_list(self, db_session, user_id):
        """
        Lists the cohorts belonging to a certain user that
        are available to create reports

        Parameters
            db_session      : open session to the database
            user_id         : user id of the cohort to retrieve cohorts for

        Returns
            List of Cohort objects
        """
        cohorts = self._get_list(db_session, user_id)
        cohorts = filter(lambda c: not self.is_invalid(c), cohorts)
        return cohorts

    def get_list_for_display(self, db_session, user_id):
        """
        Lists the cohorts belonging to a certain user, including invalid ones

        Parameters
            db_session      : open session to the database
            user_id         : user id of the cohort to retrieve cohorts for

        Returns
            List of Cohort objects
        """
        return self._get_list(db_session, user_id)

    def _get_list(self, db_session, user_id):
        query = db_session.query(CohortStore)\
            .join(CohortUserStore)\
            .join(UserStore)\
            .filter(UserStore.id == user_id)\
            .filter(CohortUserStore.role.in_(CohortUserRole.SAFE_ROLES))\
            .filter(CohortStore.enabled)

        return [self.convert(c) for c in query.all()]

    def is_invalid(self, cohort):
        """
        Returns
            True if this cohort should be valid but is not
            False otherwise
        """
        should_be_valid = issubclass(cohort.__class__, ValidatedCohort)
        return should_be_valid and (not cohort.validated or cohort.size == 0)

    def add_wiki_cohort(self, session, project):
        """
        Adds a wiki cohort, if it doesn't already exist.

        Parameters
            session : database session
            project : project to wrap in a wiki cohort

        Returns
            Either the existing CohortStore object, or the new one
        """
        search = CohortStore(
            name=project,
            class_name=WikiCohort.__name__,
            default_project=project,
        )
        existing = session.query(CohortStore)\
            .filter(CohortStore.name == search.name)\
            .filter(CohortStore.class_name == search.class_name)\
            .filter(CohortStore.default_project == search.default_project)\
            .first()

        if existing is None:
            search.description = 'System-added project-level cohort'
            search.enabled = True
            session.add(search)
            session.commit()
            existing = search

        return self.convert(existing)

    def share(self, session, cohort, user_id):
        """
        Shares a cohort with a user, if not already shared

        Parameters
            session : database session
            cohort  : logical cohort object
            user_id : id of a user to share the cohort with
        """
        search = CohortUserStore(
            cohort_id=cohort.id,
            user_id=user_id,
            role=CohortUserRole.VIEWER,
        )

        existing = session.query(CohortUserStore)\
            .filter(CohortUserStore.cohort_id == search.cohort_id)\
            .filter(CohortUserStore.user_id == search.user_id)\
            .first()

        if existing is None:
            session.add(search)
            session.commit()
