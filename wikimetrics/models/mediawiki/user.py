from sqlalchemy import Column, Integer, String
from wikimetrics.configurables import db
from custom_columns import MediawikiTimestamp
from sqlalchemy.dialects.mysql import TINYBLOB, VARBINARY
from wikimetrics.utils import UNICODE_NULL

__all__ = ['MediawikiUser']


class MediawikiUser(db.MediawikiBase):
    __tablename__ = 'user'
    
    # defaults are for user generating data methods
    # VARBINARY bindings are needed so the table user we create
    # in the mediawiki testing database resembles the table in production
    user_id = Column(Integer, primary_key=True)
    user_name = Column(VARBINARY(255))
    user_real_name = Column(VARBINARY(255), nullable=False, default='')
    user_password = Column(TINYBLOB, nullable=False, default='')
    user_newpassword = Column(TINYBLOB, nullable=False, default='')
    user_newpass_time = Column(MediawikiTimestamp)
    user_email = Column(String(255), nullable=False, default='')
    user_touched = Column(MediawikiTimestamp, nullable=False, default=UNICODE_NULL * 14)
    user_token = Column(String(255), nullable=False, default=UNICODE_NULL * 32)
    user_email_authenticated = Column(MediawikiTimestamp)
    user_email_token = Column(String(255))
    user_email_token_expires = Column(MediawikiTimestamp)
    user_registration = Column(MediawikiTimestamp)
    user_editcount = Column(Integer)
