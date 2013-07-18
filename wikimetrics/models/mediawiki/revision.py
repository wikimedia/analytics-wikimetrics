from sqlalchemy import Column, BigInteger, Integer, Boolean, DateTime, String, ForeignKey
from wikimetrics.configurables import db

__all__ = [
    'Revision',
]


class Revision(db.MediawikiBase):
    __tablename__ = 'revision'
    
    rev_id = Column(Integer, primary_key=True)
    rev_page = Column(Integer, ForeignKey('page.page_id'))
    rev_text_id = Column(Integer)
    rev_comment = Column(String(255))
    rev_user = Column(Integer, ForeignKey('user.user_id'))
    rev_user_text = Column(String(255))
    rev_timestamp = Column(DateTime)
    rev_minor_edit = Column(Boolean)
    rev_deleted = Column(Integer)  # this might be a boolean but it gets overflown if set that way
    rev_len = Column(BigInteger)
    rev_parent_id = Column(Integer)
    rev_sha1 = Column(String(32))
    #rev_content_model = Column(String(32))
    #rev_content_format = Column(String(64))
