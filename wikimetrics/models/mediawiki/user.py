from sqlalchemy import Column, Integer, String
from wikimetrics.configurables import db
from custom_columns import MediawikiTimestamp

__all__ = ['MediawikiUser']


class MediawikiUser(db.MediawikiBase):
    __tablename__ = 'user'
    
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    user_real_name = Column(String(255))
    # do not map: user_password
    # do not map: user_newpassword
    user_newpass_time = Column(MediawikiTimestamp)
    user_email = Column(String(255))
    user_touched = Column(MediawikiTimestamp)
    # do not map: user_token
    user_email_authenticated = Column(MediawikiTimestamp)
    # do not map: user_email_token
    # do not map: user_email_token_expires = Column(MediawikiTimestamp)
    user_registration = Column(MediawikiTimestamp)
    user_editcount = Column(Integer)
