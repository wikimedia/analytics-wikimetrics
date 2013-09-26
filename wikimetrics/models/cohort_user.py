from sqlalchemy import Column, Integer, ForeignKey, String
from wikimetrics.configurables import db

__all__ = [
    'CohortUserRole',
    'CohortUser'
]


class CohortUserRole(object):
    OWNER = 'OWNER'
    VIEWER = 'VIEWER'
    SAFE_ROLES = [OWNER, VIEWER]


class CohortUser(db.WikimetricsBase):
    """
    Represents the join table between `cohort` and `user`
    tables which stores cohort permissions.  Uses
    sqlalchemy.declarative to handle db mapping
    """
    
    __tablename__ = 'cohort_user'
    
    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer(50), ForeignKey('user.id'))
    cohort_id = Column(Integer(50), ForeignKey('cohort.id'))
    role      = Column(String(45))
    
    def __repr__(self):
        return '<CohortUser("{0}")>'.format(self.id)
