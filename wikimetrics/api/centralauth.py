from wikimetrics.configurables import db
from wikimetrics.models.centralauth import CentralAuthLocalUser as LocalUser
from wikimetrics.utils import parse_username
from wikimetrics.utils import deduplicate_by_key


class CentralAuthService(object):
    def expand_via_centralauth(self, cohort_users, ca_session):
        '''
        Tries to find users with the original user's names in other projects.
        And adds them to the cohort. So the cohort will include all projects
        of the given users. i.e. given the cohort:

        [{'raw_id_or_name': 'JSmith (WMF)', 'project': 'enwiki'}]

        and considering the given user also has an account in 'dewiki' and
        'frwiktionary', it will return:

        [{'raw_id_or_name': 'JSmith (WMF)', 'project': 'enwiki'},
         {'raw_id_or_name': 'JSmith (WMF)', 'project': 'dewiki'},
         {'raw_id_or_name': 'JSmith (WMF)', 'project': 'frwiktionary'}]

        The method uses the centralauth database for that.
        If a cohort user is not in the centralauth localuser table,
        it will be returned as is.

        Parameters
            cohot_users : List of cohort users, formatted like
                          {'raw_id_or_name': raw_id_or_name, 'project': project}
            ca_session  : Centralauth database session

        Returns
            List of expanded cohort users, formatted like
            {'raw_id_or_name': raw_id_or_name, 'project': project}.
        '''
        expanded_cohort = set([])
        for cohort_user in cohort_users:
            user_tuple = (cohort_user['raw_id_or_name'], cohort_user['project'])
            expanded_cohort.add(user_tuple)

            ca_local_users = (
                ca_session
                .query(LocalUser.lu_name, LocalUser.lu_wiki)
                .filter(LocalUser.lu_name == cohort_user['raw_id_or_name']).all()
            )
            if len(ca_local_users) > 0:
                ca_local_users = set([(x[0], x[1]) for x in ca_local_users])
                expanded_cohort = expanded_cohort.union(ca_local_users)

        expanded_cohort = [{
            'raw_id_or_name' : x[0],
            'project'  : x[1]
        } for x in expanded_cohort]
        expanded_cohort.sort(key=lambda x: [x['raw_id_or_name'], x['project']])
        return expanded_cohort
