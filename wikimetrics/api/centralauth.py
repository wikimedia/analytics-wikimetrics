from wikimetrics.configurables import db
from wikimetrics.models.centralauth import CentralAuthLocalUser as LocalUser
from wikimetrics.utils import parse_username
from wikimetrics.utils import deduplicate_by_key


class CentralAuthService(object):
    def expand_via_centralauth(self, cohort_users, ca_session, default_project):
        '''
        Returns all centralauth local users (name, project)
        that share the name with the passed cohort users.
        If a cohort user is not in the centralauth localuser table
        it will be returned as is.
        '''
        expanded_cohort = set([])
        for cohort_user in cohort_users:
            username = parse_username(cohort_user[0])
            if len(cohort_user) > 1:
                project = cohort_user[-1]
            else:
                project = default_project
            expanded_cohort.add((username, project))

            ca_local_users = (
                ca_session
                .query(LocalUser.lu_name, LocalUser.lu_wiki)
                .filter(LocalUser.lu_name == username).all()
            )
            if len(ca_local_users) > 0:
                ca_local_users = set([(x[0], x[1]) for x in ca_local_users])
                expanded_cohort = expanded_cohort.union(ca_local_users)

        expanded_cohort = [list(x) for x in expanded_cohort]
        return sorted(expanded_cohort)
