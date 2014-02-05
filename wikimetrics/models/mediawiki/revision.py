from sqlalchemy import Column, BigInteger, Integer, Boolean, String, ForeignKey
from wikimetrics.configurables import db
from custom_columns import MediawikiTimestamp

__all__ = ['Revision']


class Revision(db.MediawikiBase):
    __tablename__ = db.config['REVISION_TABLENAME']
    
    rev_id = Column(Integer, primary_key=True)
    rev_page = Column(Integer, ForeignKey('page.page_id'), nullable=False, default=0)
    rev_text_id = Column(Integer, nullable=False, default=0)
    rev_comment = Column(String(255), nullable=False, default='')
    rev_user = Column(Integer, ForeignKey('user.user_id'), nullable=False, default=0)
    rev_user_text = Column(String(255), nullable=False, default='')
    rev_timestamp = Column(MediawikiTimestamp, nullable=False,
                           default=u'\0\0\0\0\0\0\0\0\0\0\0\0\0\0')
    rev_minor_edit = Column(Integer, nullable=False, default='0')
    # this might be a boolean but it gets overflown if set that way
    rev_deleted = Column(Integer)
    rev_len = Column(BigInteger)
    rev_parent_id = Column(Integer)
    rev_sha1 = Column(String(32))
    rev_content_model = Column(String(32))
    rev_content_format = Column(String(64))
