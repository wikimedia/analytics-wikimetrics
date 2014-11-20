from sqlalchemy import Column, Integer, Boolean
from sqlalchemy.dialects.mysql import TINYBLOB, VARBINARY

from wikimetrics.configurables import db
from wikimetrics.utils import UNICODE_NULL
from custom_columns import MediawikiTimestamp


class Archive(db.MediawikiBase):
    """
    Full table definition is not needed, but here it is for reference:
    +---------------+---------------------+------+-----+---------+-------+
    | Field         | Type                | Null | Key | Default | Extra |
    +---------------+---------------------+------+-----+---------+-------+
    | ar_id         | int(10) unsigned    | NO   |     | 0       |       |
    | ar_namespace  | int(11)             | NO   |     | 0       |       |
    | ar_title      | varbinary(255)      | NO   |     |         |       |
    | ar_text       | binary(0)           | YES  |     | NULL    |       |
    | ar_comment    | binary(0)           | YES  |     | NULL    |       |
    | ar_user       | bigint(10) unsigned | YES  |     | NULL    |       |
    | ar_user_text  | varbinary(255)      | YES  |     | NULL    |       |
    | ar_timestamp  | varbinary(14)       | NO   |     |         |       |
    | ar_minor_edit | tinyint(1)          | NO   |     | 0       |       |
    | ar_flags      | tinyblob            | NO   |     | NULL    |       |
    | ar_rev_id     | int(8) unsigned     | YES  |     | NULL    |       |
    | ar_text_id    | bigint(10) unsigned | YES  |     | NULL    |       |
    | ar_deleted    | tinyint(1) unsigned | NO   |     | 0       |       |
    | ar_len        | bigint(10) unsigned | YES  |     | NULL    |       |
    | ar_page_id    | int(10) unsigned    | YES  |     | NULL    |       |
    | ar_parent_id  | int(10) unsigned    | YES  |     | NULL    |       |
    | ar_sha1       | varbinary(32)       | YES  |     | NULL    |       |
    +---------------+---------------------+------+-----+---------+-------+
    """
    __tablename__ = db.config['ARCHIVE_TABLENAME']

    ar_id         = Column(Integer, primary_key=True)
    ar_namespace  = Column(Integer, nullable=False, default=0)
    ar_title      = Column(VARBINARY(255), nullable=False, default='')
    ar_user       = Column(Integer)
    ar_user_text  = Column(VARBINARY(255))
    ar_timestamp  = Column(MediawikiTimestamp, nullable=False, default=UNICODE_NULL * 14)
    ar_minor_edit = Column(Boolean, nullable=False, default=False)
    ar_flags      = Column(TINYBLOB, nullable=False, default='')
    ar_rev_id     = Column(Integer, nullable=True)
    ar_deleted    = Column(Boolean, nullable=False, default=False)
    ar_page_id    = Column(Integer, nullable=True)
    ar_parent_id  = Column(Integer, nullable=True)
