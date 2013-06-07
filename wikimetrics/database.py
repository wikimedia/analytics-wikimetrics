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

SQL_ECHO = True

engine = create_engine('sqlite:///:memory:', echo=SQL_ECHO)
Session = sessionmaker(bind=engine)
Base = declarative_base()

#mediawiki_engine = create_engine('mysql://test:test@localhost/mediawiki', echo=True)
mediawiki_engine = create_engine('sqlite:///:memory:', echo=SQL_ECHO)
MediawikiSession = sessionmaker(bind=mediawiki_engine)
MediawikiBase = declarative_base()


def init_db():
    import wikimetrics.models
    Base.metadata.create_all(bind=engine)
    
    import wikimetrics.models.mediawiki
    MediawikiBase.metadata.create_all(bind=mediawiki_engine)
