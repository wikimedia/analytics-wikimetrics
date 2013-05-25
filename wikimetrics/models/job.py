from sqlalchemy import Column, Integer, String, ForeignKey

from usermetrics.database import Base

class Job(Base):
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
