from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.dialects.mysql import VARBINARY
from wikimetrics.configurables import db


class WikiUserStore(db.WikimetricsBase):
    """
    This class represents mediawiki users which compose
    cohorts.  A user is defined as a username or user_id
    along with the project name on which that user registered.
    This class is mapped to the wiki_user table using
    sqlalchemy.declarative
    """

    __tablename__ = 'wiki_user'

    id                  = Column(Integer, primary_key=True)
    raw_id_or_name      = Column(VARBINARY(255))
    mediawiki_username  = Column(String(255))
    mediawiki_userid    = Column(Integer)
    project             = Column(String(45))
    # valid = None means it's not been validated yet
    # valid = True means it's valid
    # valid = False means it's invalid
    valid               = Column(Boolean, default=None)
    reason_invalid      = Column(String(200))
    # The cohort id that this wikiuser is being validated for
    validating_cohort   = Column(Integer)

    __table_args__ = (
        UniqueConstraint(
            project, mediawiki_userid, validating_cohort,
            name='ix_wiki_user_project'
        ),
    )

    def __repr__(self):
        return '<WikiUserStore("{0}")>'.format(self.id)


class WikiUserKey(object):
    """
    Create this class from the three things that uniquely identify a user in the
    wiki_user table: cohort_id, mediawiki project, mediawiki user id.  An instance
    of this class will have a string representation that can be parsed back into an
    instance.  This enables writing and reading dictionaries of results by users to
    permanent storage.
    """
    SEPARATOR = '|'
    
    def __init__(self, user_id, user_project, cohort_id):
        self.user_id = str(user_id)
        self.user_project = str(user_project)
        self.cohort_id = str(cohort_id)
    
    @classmethod
    def fromstr(cls, wiki_user_key_str):
        user_id, user_project, cohort_id = wiki_user_key_str.split(WikiUserKey.SEPARATOR)
        return cls(user_id, user_project, cohort_id)
    
    def __repr__(self):
        return WikiUserKey.SEPARATOR.join(
            (self.user_id, self.user_project, self.cohort_id)
        )
        
    def __hash__(self):
        # using tuples to hash using internal hashing mechanism as much as possible
        return hash(((self.user_id, self.user_project), self.cohort_id))
        
    def __eq__(self, other):
        return (other.user_id == self.user_id and other.user_project == self.user_project
                and other.cohort_id == self.cohort_id)
