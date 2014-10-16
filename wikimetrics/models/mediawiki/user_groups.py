from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.mysql import VARBINARY

from wikimetrics.configurables import db


class MediawikiUserGroups(db.MediawikiBase):
    __tablename__ = 'user_groups'

    ug_user = Column(
        Integer, ForeignKey('user.user_id'), nullable=False, default=0, primary_key=True
    )
    ug_group = Column(VARBINARY(255), nullable=False, primary_key=True)
