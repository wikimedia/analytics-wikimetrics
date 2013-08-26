from sqlalchemy import Column, Integer, String, Boolean
from wikimetrics.configurables import db

__all__ = [
    'User',
    'UserRole',
]


class UserRole(object):
    ADMIN = 'ADMIN'
    USER = 'USER'
    GUEST = 'GUEST'


class User(db.WikimetricsBase):
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
    google_id = Column(String(254))
    
    # Flask-Login properties
    authenticated = Column(Boolean, default=False)
    active = Column(Boolean, default=False)
    
    @staticmethod
    def get(session, user_id):
        user = session.query(User).get(user_id)
        if user:
            session.expunge(user)
        return user
    
    def login(self, session):
        """
        Sets the properties that Flask depends on.
        Important: caller should remove this instance from the database session so it
        can behave properly in Flask-Login.
        """
        self.authenticated = True
        self.active = True
        session.commit()
    
    def logout(self, session):
        """
        Adds this instance back to the session passed in, logs it out,
        and saves it to the db.
        Important: caller might want to remove this instance from the
        database session so it can behave properly in Flask-Login.
        """
        session.add(self)
        self.authenticated = False
        self.active = False
        session.commit()
    
    def detach_from(self, session):
        """
        Removes this instance from the session passed in.
        """
        session.expunge(self)
    
    def is_authenticated(self):
        return self.authenticated
    
    def is_active(self):
        return self.active
    
    def is_anonymous(self):
        return not self.authenticated
    
    def get_id(self):
        """
        Flask-Login needs a method by this name
        to return a unicode id.
        """
        return unicode(self.id)

    def __repr__(self):
        return '<User("{0}")>'.format(self.id)
