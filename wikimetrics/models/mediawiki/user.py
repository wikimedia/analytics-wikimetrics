from sqlalchemy import Column, Integer, Boolean, DateTime, String
from wikimetrics.configurables import db

__all__ = [
    'MediawikiUser',
]

class MediawikiUser(db.MediawikiBase):
    __tablename__ = 'user'
    
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    user_real_name = Column(String(255))
    user_password = None#TODO: Password? = Column(String(255))
    user_newpassword = None#TODO: Password? = Column(String(255))
    user_newpass_time = Column(DateTime)
    user_email = Column(String(255))
    user_touched = Column(DateTime)
    user_token = None#TODO: Token? binary(32) DEFAULT NULL,
    user_email_authenticated = Column(DateTime)
    user_email_token = None#TODO: Token? binary(32) DEFAULT NULL,
    user_email_token_expires = Column(DateTime)
    user_registration = Column(DateTime)
    user_editcount = Column(Integer)
