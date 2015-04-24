from sqlalchemy import Column, Integer, ForeignKey, String
from wikimetrics.configurables import db


class CohortTagStore(db.WikimetricsBase):
    """
    Represents the join table between `cohort` and `tag`
    tables to map tags to cohorts.  Uses
    sqlalchemy.declarative to handle db mapping
    """

    __tablename__ = 'cohort_tag'

    id        = Column(Integer, primary_key=True)
    tag_id    = Column(Integer, ForeignKey('tag.id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)

    def __repr__(self):
        return '<CohortTagStore("{0}")>'.format(self.id)
