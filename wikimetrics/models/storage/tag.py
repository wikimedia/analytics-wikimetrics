from sqlalchemy import Column, Integer, String
from wikimetrics.configurables import db


class TagStore(db.WikimetricsBase):
    # TODO: Write description

    __tablename__ = 'tag'

    id      = Column(Integer, primary_key=True)
    name    = Column(String(50), nullable=False, default='')

    def __repr__(self):
        return '<TagStore("{0}")>'.format(self.id)
