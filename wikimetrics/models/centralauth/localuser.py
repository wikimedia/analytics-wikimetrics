from sqlalchemy import Column
from sqlalchemy.dialects.mysql import VARBINARY, ENUM
from wikimetrics.configurables import db


__all__ = ['CentralAuthLocalUser']


class CentralAuthLocalUser(db.CentralAuthBase):
    __tablename__ = 'localuser'
    lu_wiki = Column(VARBINARY(255), primary_key=True)
    lu_name = Column(VARBINARY(255), primary_key=True)
    lu_attached_timestamp = Column(VARBINARY(14))
    lu_attached_method = Column(ENUM('primary',
                                     'empty',
                                     'mail',
                                     'password',
                                     'admin',
                                     'new',
                                     'login'))
