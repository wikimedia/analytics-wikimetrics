from wikimetrics.configurables import db
from wikimetrics.models.centralauth import CentralAuthLocalUser as LocalUser
from wikimetrics.utils import parse_username
from wikimetrics.utils import deduplicate_by_key


class CentralAuthService(object):
    def expand_via_centralauth(self, cohort_users, ca_session):
        '''
        Returns all centralauth local users (name, project)
        that share the name with the passed cohort users.
        If a cohort user is not in the centralauth localuser table
        it will be returned as is.
        '''
        deduplicated = deduplicate_by_key(cohort_users, lambda x: x[0])
        expanded_cohort_users = []
        for cohort_user in deduplicated:
            username = parse_username(cohort_user[0])
            ca_local_users = (
                ca_session.
                query(LocalUser.lu_name, LocalUser.lu_wiki).
                filter(LocalUser.lu_name == username).all()
            )
            if len(ca_local_users) > 0:
                ca_local_users = [list(x) for x in ca_local_users]
                expanded_cohort_users.extend(ca_local_users)
            else:
                expanded_cohort_users.append(cohort_user)
        return expanded_cohort_users
