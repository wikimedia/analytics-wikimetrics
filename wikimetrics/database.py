from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()

def init_db():
    import wikimetrics.models
    Base.metadata.create_all(bind=engine)
