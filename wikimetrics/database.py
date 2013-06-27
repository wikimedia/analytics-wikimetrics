"""
This module deals with database connections, engine creation, and session creation.
It exposes methods and variables according to SQLAlchemy best practices (hopefully).
It has the ability to connect to multiple mediawiki databases.
It uses Flask's handy config module to configure itself.
"""
import json
from os.path import exists
from os import remove
from urllib2 import urlopen
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    'Database',
]


class SerializableBase(object):
    
    def _asdict(self):
        """ simplejson (used by flask.jsonify) looks for a method with this name """
        return {c.name : getattr(self, c.name) for c in self.__table__.columns if c.name != 'id'}


class Database(object):
    """
    Basically a collection of all database related objects and methods.
    Instantiated after configuration is done, in the wikimetrics.configurables module.
    You should not instantiate this yourself, just do `from .configurables import db`
    """
    
    def __init__(self):
        """
        Initializes the config object (using Flask's Config class).
        Sets the root_path of the Config object to '' which means you must provide
        absolute paths to any `config.from_pyfile` calls.
        
        Initializes the declarative bases that are used throughout the project.
        Initializes the empty engines and sessionmakers that support
        `get_session` and `get_mw_session`.
        """
        self.WikimetricsBase = declarative_base(cls=SerializableBase)
        self.MediawikiBase = declarative_base(cls=SerializableBase)

        self.wikimetrics_engine = None
        self.wikimetrics_sessionmaker = None
        
        self.mediawiki_engines = {}
        self.mediawiki_sessionmakers = {}
        self.project_host_map = self.get_project_host_map()
    
    def get_session(self):
        """
        On the first run, instantiates the Wikimetrics session maker
        and create wikimetrics tables if they don't exist.
        On subsequent runs, it does not re-define the session maker or engine.
        
        Returns:
            new sqlalchemy session open to the wikimetrics database
        """
        if not self.wikimetrics_engine:
            self.wikimetrics_engine = create_engine(
                self.config['WIKIMETRICS_ENGINE_URL'],
                echo=self.config['SQL_ECHO'],
            )
            self.wikimetrics_sessionmaker = sessionmaker(self.wikimetrics_engine)
            
            # This import is necessary here so WikimetricsBase knows about all its children.
            import wikimetrics.models
            self.WikimetricsBase.metadata.create_all(self.wikimetrics_engine)
        
        return self.wikimetrics_sessionmaker()
    
    def get_mw_session(self, project):
        """
        Based on the mediawiki project passed in, create a sqlalchemy session.
        
        Parameters:
            project : string name of the mediawiki project (for example: enwiki, arwiki)
        
        Returns:
            new sqlalchemy session connected to the appropriate database.  As an optimization,
            this method caches sqlalchemy session makers and creates sessions from those.
        """
        if project in self.mediawiki_sessionmakers:
            return self.mediawiki_sessionmakers[project]()
        else:
            engine = self.get_mw_engine(project)
            # TODO: this should probably check before calling create_all
            import wikimetrics.models.mediawiki
            self.MediawikiBase.metadata.create_all(engine)
            
            project_sessionmaker = sessionmaker(engine)
            self.mediawiki_sessionmakers[project] = project_sessionmaker
            return project_sessionmaker()
    
    def get_mw_engine(self, project):
        """
        Based on the mediawiki project passed in, create a sqlalchemy engine.
        
        Parameters:
            project : string name of the mediawiki project (for example: enwiki, arwiki)
        
        Returns:
            new or cached sqlalchemy engine connected to the appropriate database.
        """
        if project in self.mediawiki_engines:
            return self.mediawiki_engines[project]
        else:
            engine = create_engine(
                self.config['MEDIAWIKI_ENGINE_URL_TEMPLATE'].format(project),
                echo=self.config['SQL_ECHO'],
            )
            self.mediawiki_engines[project] = engine
            return engine
    
    def get_project_host_map(self, usecache=True):
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
