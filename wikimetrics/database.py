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

PROJECT_HOST_MAP = get_project_host_map()

engine = create_engine('sqlite:///:memory:', echo=SQL_ECHO)
Session = sessionmaker(bind=engine)
Base = declarative_base()
MediawikiBase = declarative_base()

#mediawiki_engine = create_engine('mysql://test:test@localhost/mediawiki', echo=True)
# MediawikiSession = sessionmaker(bind=mediawiki_engine)
#MEDIAWIKI_ENGINES = project : create_engine('sqlite:///:memory:', echo=SQL_ECHO)\
        #for project, url in PROJECT_HOST_MAP.iteritems()}
#MEDIAWIKI_SESSIONS = project : sessionmaker(bind=engine)\
        #for project, engine in MEDIAWIKI_ENGINES.iteritems()}

MEDIAWIKI_ENGINES = {}
MEDIAWIKI_SESSIONMAKERS = {}
TEST_PROJECTS = ['enwiki', 'arwiki']


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
        session_factory = sessionmaker(bind=engine)
        MEDIAWIKI_SESSIONMAKERS[project] = session_factory
        # TODO: check whether we should return the class or instance
        session = session_factory()
        return session


def init_db():
    import wikimetrics.models
    Base.metadata.create_all(bind=engine)
    
    # TODO: cleaner test switch which grabs TEST_WIKIS from a config
    import wikimetrics.models.mediawiki
    for project in TEST_PROJECTS:
        MediawikiBase.metadata.create_all(bind=get_engine(project))


