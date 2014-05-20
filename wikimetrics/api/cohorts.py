from wikimetrics.exceptions import Unauthorized
from wikimetrics.models.storage import (
    CohortStore, CohortUserStore, UserStore, CohortUserRole
)


class CohortService(object):
    """
    General service that helps manage cohorts
    """
    
    def get(self, db_session, user_id, by_id=None, by_name=None):
        """
        Gets a cohort but first checks permissions on it
        
        Parameters
            db_session  : the database session to query
            user_id     : the user that should have access to the cohort
            by_id       : the cohort id to get.  <by_id> or <by_name> is True
            by_name     : the cohort name to get.  <by_id> or <by_name> is True
        
        Returns
            If found, a CohortStore instance with id == cohort_id or name == cohort_name
        
        Raises
            NoResultFound   : cohort did not exist
            Unauthorized    : user_id is not allowed to access this cohort
        """
        query = db_session.query(CohortStore, CohortUserStore.role)\
            .join(CohortUserStore)\
            .join(UserStore)\
            .filter(UserStore.id == user_id)\
            .filter(CohortStore.enabled)
        
        if by_id is not None:
            query = query.filter(CohortStore.id == by_id)
        if by_name is not None:
            query = query.filter(CohortStore.name == by_name)
        
        cohort, role = query.one()
        if role in CohortUserRole.SAFE_ROLES:
            return cohort
        else:
            raise Unauthorized('You are not allowed to use this cohort')
