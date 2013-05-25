from sqlalchemy import Column, Integer, Boolean, DateTime, String

from usermetrics.database import Base

class Cohort(Base):
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
