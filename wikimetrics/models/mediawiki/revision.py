from sqlalchemy import Column, BigInteger, Integer, Boolean, String, ForeignKey
from wikimetrics.configurables import db
from custom_columns import MediawikiTimestamp

__all__ = ['Revision']


class Revision(db.MediawikiBase):
    __tablename__ = 'revision_userindex'
    
    rev_id = Column(Integer, primary_key=True)
    rev_page = Column(Integer, ForeignKey('page.page_id'))
    rev_text_id = Column(Integer)
    rev_comment = Column(String(255))
    rev_user = Column(Integer, ForeignKey('user.user_id'))
    rev_user_text = Column(String(255))
    rev_timestamp = Column(MediawikiTimestamp)
    rev_minor_edit = Column(Boolean)
    # this might be a boolean but it gets overflown if set that way
    rev_deleted = Column(Integer)
    rev_len = Column(BigInteger)
    rev_parent_id = Column(Integer)
    rev_sha1 = Column(String(32))
    #rev_content_model = Column(String(32))
    #rev_content_format = Column(String(64))
