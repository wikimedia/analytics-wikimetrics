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
    """
    This class represent website users, who can have permissions
    and cohort ownership. It is also mapped to the `user` table
    using sqlalchemy.declarative
    """
    
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(254))
    role = Column(String(50), default=UserRole.GUEST)

    def __repr__(self):
        return '<User("{0}")>'.format(self.id)
