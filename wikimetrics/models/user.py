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
    This class represents website users, who can have permissions
    and cohort ownership. It is also mapped to the `user` table
    using sqlalchemy.declarative
    It also defines methods required by Flask-Login.
    """
    
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(254))
    role = Column(String(50), default=UserRole.GUEST)
    
    # Flask-Login properties
    authenticated = False
    active = False

    def __repr__(self):
        return '<User("{0}")>'.format(self.id)
    
    def is_authenticated(self):
        return self.authenticated
    
    def is_active(self):
        return self.active
    
    def is_anonymouse(self):
        return not self.authenticated
    
    def get_id(self):
        return unicode(self.id)
