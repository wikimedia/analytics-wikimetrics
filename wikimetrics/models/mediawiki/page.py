from sqlalchemy import Column, Integer, Boolean, String
from wikimetrics.configurables import db
from custom_columns import MediawikiTimestamp
from sqlalchemy.dialects.mysql import DOUBLE, TINYBLOB, TINYINT

__all__ = ['Page']


class Page(db.MediawikiBase):
    __tablename__ = 'page'
    
    page_id = Column(Integer, primary_key=True)
    page_namespace = Column(Integer, nullable=False, default=0)
    page_title = Column(String(255), nullable=False, default='')
    page_restrictions = Column(TINYBLOB, nullable=False, default='')   # TODO: default?
    page_counter = Column(Integer, nullable=False, default=0)
    page_is_redirect = Column(TINYBLOB, nullable=False, default=0)
    page_is_new = Column(Boolean, nullable=False, default=0)
    page_random = Column(DOUBLE, nullable=False, default=0)
    page_touched = Column(MediawikiTimestamp, default=u'\0\0\0\0\0\0\0\0\0\0\0\0\0\0')
    page_latest = Column(Integer, nullable=False, default=0)
    page_len = Column(Integer, nullable=False, default=0)
