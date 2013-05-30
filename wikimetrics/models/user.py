from sqlalchemy import Column, Integer, String
from wikimetrics.database import Base

__all__ = [
    'User',
    'UserRole',
]

class UserRole(object):
    ADMIN = 'ADMIN'
    USER_WITH_NDA = 'USER_WITH_NDA'
    USER_WITHOUT_NDA = 'USER_WITHOUT_NDA'
    GUEST = 'GUEST'

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(254))
    role = Column(String(50))

    def __init__(self,
            username = None,
            email = None,
            role = UserRole.GUEST,
        ):
        self.username = username
        self.email = email
        self.role = role

    def __repr__(self):
        return '<User("{0}")>'.format(self.id)
