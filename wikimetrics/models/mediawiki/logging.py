from sqlalchemy import Column, Integer, Boolean, DateTime, String, ForeignKey
from wikimetrics.database import MediawikiBase

__all__ = [
    'Logging',
]

class Logging(MediawikiBase):
    __tablename__ = 'logging'
    
    log_id = Column(Integer, primary_key=True)
    log_type = Column(String(32))
    log_action = Column(String(32))
    log_timestamp = Column(DateTime)
    log_user = Column(Integer, ForeignKey('user'))
    log_user_text = Column(String(255))
    log_namespace = Column(Integer)
    log_title = Column(String(255))
    log_page = Column(Integer, ForeignKey('page'))
    log_comment = Column(String(255))
    #log_params blob NOT NULL,
    log_deleted = Column(Boolean)
