from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    'Base',
    'init_db',
]

engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    import wikimetrics.models
    Base.metadata.create_all(bind=engine)
