from sqlalchemy import Column, Integer, Boolean, DateTime, String
from wikimetrics.database import Base

__all__ = [
    'Cohort',
]

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
    
    def __init__(self,
            name = None,
            description = None,
            default_project = None,
            created = None,
            enabled = True,
            public = False
        ):
        self.name = name
        self.description = description
        self.default_project = default_project
        self.created = created
        self.enabled = enabled
        self.public = public
    
    
    def __repr__(self):
        return '<Cohort("{0}")>'.format(self.id)
    
    def __iter__(self):
        # TODO: not this
        return ['dan','evan'].__iter__()
