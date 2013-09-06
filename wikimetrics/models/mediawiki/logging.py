from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from wikimetrics.configurables import db
from custom_columns import MediawikiTimestamp

__all__ = ['Logging']


class Logging(db.MediawikiBase):
    __tablename__ = 'logging'
    
    log_id = Column(Integer, primary_key=True)
    log_type = Column(String(32))
    log_action = Column(String(32))
    log_timestamp = Column(MediawikiTimestamp)
    log_user = Column(Integer, ForeignKey('user.user_id'))
    log_user_text = Column(String(255))
    log_namespace = Column(Integer)
    log_title = Column(String(255))
    log_page = Column(Integer, ForeignKey('page.page_id'))
    log_comment = Column(String(255))
    #log_params blob NOT NULL,
    log_deleted = Column(Boolean)
