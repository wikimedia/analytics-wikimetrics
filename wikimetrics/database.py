import json
from os.path import exists
from urllib2 import urlopen
from config import SQL_ECHO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    'Base',
    'MediawikiBase',
    'Session',
    'init_db',
    'get_mw_session',
]

engine = create_engine('sqlite:///:memory:', echo=SQL_ECHO)
Session = sessionmaker(engine)
Base = declarative_base()
MediawikiBase = declarative_base()


def init_db():
    import wikimetrics.models
    Base.metadata.create_all(engine)


def get_engine(project):
    if project in MEDIAWIKI_ENGINES:
        return MEDIAWIKI_ENGINES[project]
    else:
        engine = create_engine('sqlite:///:memory:', echo=SQL_ECHO)
        MEDIAWIKI_ENGINES[project] = engine
        return engine


def get_mw_session(project):
    if project in MEDIAWIKI_SESSIONMAKERS:
        return MEDIAWIKI_SESSIONMAKERS[project]()
    else:
        engine = get_engine(project)
        # TODO: this should probably check before calling create_all
        import wikimetrics.models.mediawiki
        MediawikiBase.metadata.create_all(engine)
        
        session_factory = sessionmaker(engine)
        MEDIAWIKI_SESSIONMAKERS[project] = session_factory
        # TODO: check whether we should return the class or instance
        session = session_factory()
        return session

def get_project_host_map(usecache=True):
    cache_name = 'project_host_map.json'
    if not exists(cache_name) or not usecache:
        cluster_url_fmt = 'http://noc.wikimedia.org/conf/s%d.dblist'
        host_fmt = 's%d'
        project_host_map = {}
        for i in range(1,8):
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
