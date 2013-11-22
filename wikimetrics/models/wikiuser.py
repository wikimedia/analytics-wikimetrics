from sqlalchemy import Column, Integer, String, Boolean
from wikimetrics.configurables import db

__all__ = [
    'WikiUser',
]


class WikiUser(db.WikimetricsBase):
    """
    This class represents mediawiki users which compose
    cohorts.  A user is defined as a username or user_id
    along with the project name on which that user registered.
    This class is mapped to the wiki_user table using
    sqlalchemy.declarative
    """
    
    __tablename__ = 'wiki_user'
    
    id                  = Column(Integer, primary_key=True)
    mediawiki_username  = Column(String(255))
    mediawiki_userid    = Column(Integer(50))
    project             = Column(String(45))
    # valid = None means it's not been validated yet
    # valid = True means it's valid
    # valid = False means it's invalid
    valid               = Column(Boolean, default=None)
    reason_invalid      = Column(String(200))
    # The cohort id that this wikiuser is being validated for
    validating_cohort   = Column(Integer)
    
    def __repr__(self):
        return '<WikiUser("{0}")>'.format(self.id)
