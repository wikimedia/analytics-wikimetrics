from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    'Base',
    'MediawikiBase',
    'init_db',
    'Session',
    'MediawikiSession',
]

engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

mediawiki_engine = create_engine('mysql://test:test@localhost/mediawiki', echo=True)
MediawikiSession = sessionmaker(bind=mediawiki_engine)
MediawikiBase = declarative_base()


def init_db():
    import wikimetrics.models
    Base.metadata.create_all(bind=engine)
