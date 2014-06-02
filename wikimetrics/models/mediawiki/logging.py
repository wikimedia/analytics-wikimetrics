from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from wikimetrics.configurables import db
from custom_columns import MediawikiTimestamp
from sqlalchemy.dialects.mysql import BLOB, VARBINARY

__all__ = ['Logging']


class Logging(db.MediawikiBase):
    __tablename__ = 'logging'
    
    log_id = Column(Integer, primary_key=True)
    log_type = Column(VARBINARY(32), nullable=False, default='')
    log_action = Column(VARBINARY(32), nullable=False, default='')
    log_timestamp = Column(MediawikiTimestamp, nullable=False, default=u'19700101000000')
    log_user = Column(Integer, ForeignKey('user.user_id'), nullable=False, default=0)
    log_namespace = Column(Integer, nullable=False, default=0)
    log_title = Column(VARBINARY(255), nullable=False, default='')
    log_comment = Column(VARBINARY(255), nullable=False, default='')
    log_params = Column(BLOB, nullable=False, default='')
    log_deleted = Column(Boolean, nullable=False, default=0)
    log_user_text = Column(VARBINARY(255), nullable=False, default='')
    log_page = Column(Integer, ForeignKey('page.page_id'))
