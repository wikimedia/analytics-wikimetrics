from sqlalchemy import Column, Integer, Boolean, String
from wikimetrics.configurables import db
from custom_columns import MediawikiTimestamp

__all__ = ['Page']


class Page(db.MediawikiBase):
    __tablename__ = 'page'
    
    page_id = Column(Integer, primary_key=True)
    page_namespace = Column(Integer)
    page_title = Column(String(255))
    page_restrictions = None  # TODO: tinyblob NOT NULL,
    page_counter = None  # TODO: bigint(20) unsigned NOT NULL DEFAULT '0',
    page_is_redirect = Column(Boolean)
    page_is_new = Column(Boolean)
    page_random = None  # TODO: double unsigned NOT NULL,
    page_touched = Column(MediawikiTimestamp)
    page_latest = Column(Integer)
    page_len = Column(Integer)
    page_content_model = Column(String(32))
