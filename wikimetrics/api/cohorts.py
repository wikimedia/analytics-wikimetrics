from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func
from wikimetrics.configurables import db
from wikimetrics.exceptions import Unauthorized, InvalidCohort, DatabaseError
from wikimetrics.models import cohort_classes, ValidatedCohort, WikiCohort
from wikimetrics.models.storage import (
    CohortStore, CohortUserStore, UserStore,
    WikiUserStore, WikiUserKey, CohortWikiUserStore,
    CohortTagStore
)
from wikimetrics.enums import CohortUserRole


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
    def get_wikiusers(self, cohort, session, limit=None):
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

            return c.filter_wikiuser_query(
                session.query(WikiUserStore)).limit(limit).all()
        else:
            return list(c)

    def get_wikiusernames_for_cohort(self, cohort_id, session):
        """
        Convenience function for the UI to retrieve
        wikiuser names given a cohort_id

        Parameters:
            cohort_id
            session
        Returns:
            Dictionary keyed by WikiUserKey or empty dictionary
            if records not found.
        """
        user_names = {}

        try:
            results = session.query(WikiUserStore.mediawiki_username,
                                    WikiUserStore.project,
                                    WikiUserStore.mediawiki_userid)\
                .filter(WikiUserStore.validating_cohort == cohort_id).all()

        except NoResultFound:
            return user_names

        for r in results:
            user_names[WikiUserKey(r[2], r[1], cohort_id)] = r[0]

        return user_names

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

    def get_cohort_by_name(self, db_session, name):
        """
        Gets a cohort by name, without worrying about access, ownership or duplicates.
        """
        return db_session.query(CohortStore).filter(CohortStore.name == name).first()

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

    def is_owned_by_user(self, db_session, cohort_id, user_id, raise_errors=False):
        """
        Returns True if the user is the owner of the cohort.
        Returns False otherwise.
        """
        try:
            # _get method will raise Unauthorized error
            # if the user is not the owner of the cohort
            self._get(db_session, user_id, by_id=cohort_id)
            return True
        except Unauthorized, e:
            if raise_errors:
                raise e
            return False

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
            True if this cohort should be validated and valid
            to be used but is not
            False otherwise
        """
        return cohort.has_validation_info and (not cohort.validated or cohort.size == 0)

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

    def get_validation_info(self, cohort, session):
        """
        Returns
            If the cohort has no validation information, an empty dictionary
            Otherwise, a dictionary with cohort validation stats:

            invalid_count       : number of invalid users
            valid_count         : number of valid users
            total_count         : number of users in the cohort
            not_validated_count : users in the cohort not yet validated at all
        """
        if not cohort.has_validation_info:
            # make UI work as little as possible, do not return nulls
            return {}

        """
            select valid, count(*)
              from wikimetrics.wiki_user
             group by valid

        Returns:
            +-------+----------+
            | valid | count(*) |
            +-------+----------+
            |  null |     1576 |
            |     0 |       61 |
            |     1 |     1593 |
            +-------+----------+

            Since valid is defined as boolean on bindings 1 and 0 are translated to
            True and False, null to None
        """

        rows = session\
            .query(WikiUserStore.valid, func.count(WikiUserStore).label('count'))\
            .filter(WikiUserStore.validating_cohort == cohort.id)\
            .group_by(WikiUserStore.valid)\
            .all()

        counts_by_valid = {r.valid : r.count for r in rows}
        stats = {
            label : counts_by_valid.get(valid, 0)
            for valid, label in {
                None: 'not_validated_count',
                True: 'valid_count',
                False: 'invalid_count'
            }.items()
        }

        stats['total_count'] = sum(stats.values())
        stats['validated_count'] = stats['valid_count'] + stats['invalid_count']

        return stats

    def get_membership(self, cohort, session):
        wikiusers = (
            session.query(
                WikiUserStore.raw_id_or_name,
                WikiUserStore.mediawiki_username,
                WikiUserStore.mediawiki_userid,
                WikiUserStore.project,
                WikiUserStore.valid,
                WikiUserStore.reason_invalid
            )
            .filter(WikiUserStore.validating_cohort == cohort.id)
            .all()
        )

        by_raw_id_or_name = {}
        for wikiuser in wikiusers:
            if wikiuser.raw_id_or_name not in by_raw_id_or_name:
                by_raw_id_or_name[wikiuser.raw_id_or_name] = {
                    'raw_id_or_name' : wikiuser.raw_id_or_name,
                    'username': wikiuser.mediawiki_username,
                    'userid' : wikiuser.mediawiki_userid,
                    'projects': [],
                    'invalidProjects': [],
                    'invalidReasons': []
                }
                
            wikiuser_info = by_raw_id_or_name[wikiuser.raw_id_or_name]
            wikiuser_info['projects'].append(wikiuser.project)
            if not wikiuser.valid:
                wikiuser_info['invalidProjects'].append(wikiuser.project)
                wikiuser_info['invalidReasons'].append(wikiuser.reason_invalid)
                # If the user is not valid, show the raw_id_or_name in the User
                # id or name column, depending on the validate_as_user_ids value.
                if cohort.validate_as_user_ids:
                    wikiuser_info['userid'] = wikiuser.raw_id_or_name
                else:
                    wikiuser_info['username'] = wikiuser.raw_id_or_name

        membership = by_raw_id_or_name.values()
        membership.sort(key=lambda x: x['username'])
        return membership

    def delete_cohort_wikiuser(
            self, raw_id_or_name, cohort_id, current_user_id,
            session, invalid_only=False):
        # raises Unauthorized error if the user has no permits on the cohort
        self.is_owned_by_user(session, cohort_id, current_user_id, True)
        wikiusers = (
            session.query(WikiUserStore)
            .join(CohortWikiUserStore)
            .filter(WikiUserStore.raw_id_or_name == raw_id_or_name)
            .filter(CohortWikiUserStore.cohort_id == cohort_id)
            .all()
        )
        ids_to_delete = []
        for x in wikiusers:
            if not invalid_only or not x.valid:
                ids_to_delete.append(x.id)
        try:
            (session
                .query(CohortWikiUserStore)
                .filter(CohortWikiUserStore.wiki_user_id.in_(ids_to_delete))
                .filter(CohortWikiUserStore.cohort_id == cohort_id)
                .delete(synchronize_session='fetch'))
            (session
                .query(WikiUserStore)
                .filter(WikiUserStore.id.in_(ids_to_delete))
                .delete(synchronize_session='fetch'))
            session.commit()
        except DatabaseError, e:
            session.rollback()
            raise e

    def get_tag(self, db_session, tag, cohort_id, user_id):
        """
        Returns cohort tag if the cohort is owned by user.
        Raises
            Unauthorized    : user_id is not allowed to access this cohort
        """
        # raises Unauthorized error if the user has no permits on the cohort
        self.is_owned_by_user(db_session, cohort_id, user_id, True)

        return db_session.query(CohortTagStore) \
            .filter(CohortTagStore.tag_id == tag.id) \
            .filter(CohortTagStore.cohort_id == cohort_id) \
            .all()

    def add_tag(self, db_session, tag, cohort_id, user_id):
        """
        Adds tag to cohort.
        Raises
            Unauthorized    : user_id is not allowed to access this cohort
        """
        # raises Unauthorized error if the user has no permits on the cohort
        self.is_owned_by_user(db_session, cohort_id, user_id, True)

        cohort_tag = CohortTagStore(
            tag_id=tag.id,
            cohort_id=cohort_id,
        )
        db_session.add(cohort_tag)
        db_session.commit()
