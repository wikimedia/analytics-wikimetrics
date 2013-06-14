from sqlalchemy import Column, Integer, String
from flask.ext.login import UserMixin
from wikimetrics.database import Base, get_session

__all__ = [
    'User',
    'UserRole',
]

class UserRole(object):
    """
    This is an enum class used to list the roles a User can have.
    """
    ADMIN = 'ADMIN'
    USER_WITH_NDA = 'USER_WITH_NDA'
    USER_WITHOUT_NDA = 'USER_WITHOUT_NDA'
    GUEST = 'GUEST'

class User(Base, UserMixin):
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
    
    def __repr__(self):
        return '<User("{0}")>'.format(self.id)
    
    @staticmethod
    def get(session, user_id):
        user = session.query(User).get(user_id)
        return user
    
    def get_id(self):
        """
        Flask-Login needs a method by this name
        to return a unicode id.
        """
        return unicode(self.id)
