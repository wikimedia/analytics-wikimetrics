from sqlalchemy import Column, Integer, Boolean, DateTime, String, ForeignKey
from wikimetrics.database import MediawikiBase

__all__ = [
    'Revision',
]

class Revision(MediawikiBase):
    __tablename__ = 'revision'
    
    rev_id = Column(Integer, primary_key=True)
    rev_page = Column(Integer, ForeignKey('page.page_id'))
    rev_text_id = Column(Integer)
    rev_comment = Column(String(255))
    rev_user = Column(Integer, ForeignKey('user.user_id'))
    rev_user_text = Column(String(255))
    rev_timestamp = Column(DateTime)
    rev_minor_edit = Column(Boolean)
    rev_deleted = Column(Boolean)
    rev_len = Column(Integer)
    rev_parent_id = Column(Integer)
    rev_sha1 = Column(String(32))
    rev_content_model = Column(String(32))
    rev_content_format = Column(String(64))
