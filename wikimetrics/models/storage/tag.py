from sqlalchemy import Column, Integer, String, UniqueConstraint
from wikimetrics.configurables import db


class TagStore(db.WikimetricsBase):
    # TODO: Write description

    __tablename__ = 'tag'

    id      = Column(Integer, primary_key=True)
    name    = Column(String(50), nullable=False, default='')

    __table_args__ = (
        UniqueConstraint(
            name,
            name='uix_tag'
        ),
    )

    def __repr__(self):
        return '<TagStore("{0}")>'.format(self.id)
