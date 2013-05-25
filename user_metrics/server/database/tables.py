from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()


class User:
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
        return '<User("{0}","{1}", "{2}")>'.format(self.username, self.email, self.is_admin)


class Job:
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    parent_job_id = Column(Integer, ForeignKey('job.id'))
    classpath = Column(String(200))

    def __init__(self, user_id, parent_job_id, classpath):
        self.user_id = user_id
        self.parent_job_id = parent_job_id
        self.classpath = classpath

    def __repr__(self):
        return '<Job("{0}","{1}", "{2}")>'.format(self.user_id, self.parent_job_id, self.classpath)


class Cohort:
    __tablename__ = 'cohort'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(254))
    default_project = Column(String(50))
    created = Column(DateTime)
    changed = Column(DateTime)
    enabled = Column(Boolean)
    public = Column(Boolean)

    def __init__(self, username, email, is_admin):
        self.name = name
        self.description = description
        self.default_project = default_project
        self.created = created
        self.changed = changed
        self.enabled = enabled
        self.public = public

    def __repr__(self):
        return '<Cohort("{0}","{1}","{2}","{3}","{4}","{5}","{6}")>'.format(self.name, self.description, self.default_project, self.created, self.changed, self.enabled, self.public)
