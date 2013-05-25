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


class WikiUser:
    __tablename__ = 'wiki_user'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    user_id = Column(Integer(50))
    project = Column(String(45))
    
    def __init__(self, username, user_id, project):
        """TODO: make this class accept either a username OR user_id"""
        self.username = username
        self.user_id = user_id
        self.project = project
    
    def __repr__(self):
        return '<WikiUser("{0}","{1}", "{2}")>'.format(self.username, self.user_id, self.project)

class CohortWikiUser:
    __tablename__ = 'wiki_user'

    id = Column(Integer, primary_key=True)
    wiki_user_id = Column(Integer(50))
    cohort_id = Column(Integer(50))

    def __init__(self, wiki_user_id, cohort_id):
        self.wiki_user_id = wiki_user_id
        self.cohort_id = cohort_id

    def __repr__(self):
        return '<CohortWikiUser("{0}","{1}")>'.format(self.wiki_user_id, self.cohort_id)


# THIS SHOULD BE IN A SEPARATE FILE
# or rather the models should be in models.py

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    #import yourapplication.models
    Base.metadata.create_all(bind=engine)
