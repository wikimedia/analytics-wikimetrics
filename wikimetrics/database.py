"""
This module deals with database connections, engine creation, and session creation.
It exposes methods and variables according to SQLAlchemy best practices (hopefully).
It has the ability to connect to multiple mediawiki databases.
"""
import json
from os.path import exists
from os import remove
from urllib2 import urlopen
from config import SQL_ECHO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    'Base',
    'MediawikiBase',
    'init_db',
    'get_session',
    'get_mw_session',
]

#engine_url = 'sqlite:///:memory:'
engine_url = 'sqlite:///test.db'
engine = create_engine(engine_url, echo=SQL_ECHO)
Session = sessionmaker(engine)
Base = declarative_base()
MediawikiBase = declarative_base()


def init_db():
    """
    Create tables for the wikimetrics database, as defined by children of the
    declarative base "Base" in the wikimetrics.models module.
    """
    import wikimetrics.models
    Base.metadata.create_all(engine)


def get_session():
    return Session()


def get_mw_engine(project):
    """
    Based on the mediawiki project passed in, create a sqlalchemy engine.
    
    Parameters:
        project : string name of the mediawiki project (for example: enwiki, commonswiki, arwiki)
    
    Returns:
        new or cached sqlalchemy engine connected to the appropriate database.
    """
    if project in MEDIAWIKI_ENGINES:
        return MEDIAWIKI_ENGINES[project]
    else:
        #engine_url = 'sqlite:///:memory:'
        engine_url = 'sqlite:///{0}.db'.format(project)
        engine = create_engine(engine_url, echo=SQL_ECHO)
        MEDIAWIKI_ENGINES[project] = engine
        return engine


def get_mw_session(project):
    """
    Based on the mediawiki project passed in, create a sqlalchemy session.
    
    Parameters:
        project : string name of the mediawiki project (for example: enwiki, commonswiki, arwiki)
    
    Returns:
        new sqlalchemy session connected to the appropriate database.  As an optimization,
        this method caches sqlalchemy session makers and creates sessions from those.
    """
    if project in MEDIAWIKI_SESSIONMAKERS:
        return MEDIAWIKI_SESSIONMAKERS[project]()
    else:
        engine = get_mw_engine(project)
        # TODO: this should probably check before calling create_all
        import wikimetrics.models.mediawiki
        MediawikiBase.metadata.create_all(engine)
        
        project_sessionmaker = sessionmaker(engine)
        MEDIAWIKI_SESSIONMAKERS[project] = project_sessionmaker
        project_session = project_sessionmaker()
        return project_session


def get_project_host_map(usecache=True):
    """
    Retrieves the list of mediawiki projects from noc.wikimedia.org.
    
    Parameters:
        usecache    : defaults to True and uses a local cache if available
    """
    cache_name = 'project_host_map.json'
    if not exists(cache_name) or not usecache:
        cluster_url_fmt = 'http://noc.wikimedia.org/conf/s%d.dblist'
        host_fmt = 's%d'
        project_host_map = {}
        # TODO: these numbers are hardcoded, is that ok?
        for i in range(1, 8):
            host = host_fmt % i
            url = cluster_url_fmt % i
            projects = urlopen(url).read().splitlines()
            for project in projects:
                project_host_map[project] = host
        json.dump(project_host_map, open(cache_name, 'w'))
    else:
        project_host_map = json.load(open(cache_name))
    return project_host_map


MEDIAWIKI_ENGINES = {}
MEDIAWIKI_SESSIONMAKERS = {}
TEST_PROJECTS = ['enwiki', 'arwiki']
PROJECT_HOST_MAP = get_project_host_map()
