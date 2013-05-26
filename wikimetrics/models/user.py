from sqlalchemy import Column, Integer, String
from wikimetrics.database import Base

__all__ = [
    'User',
]

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(254))
    role = Column(String(50))

    def __init__(self, username, email, is_admin):
        self.username = username
        self.email = email
        self.is_admin = is_admin

    def __repr__(self):
        return '<User("{0}")>'.format(self.id)
