"""
This module deals with database connections, engine creation, and session creation.
It exposes methods and variables according to SQLAlchemy best practices (hopefully).
It has the ability to connect to multiple mediawiki databases.
It uses Flask's handy config module to configure itself.
"""
import json
import os

from threading import Lock
from os.path import exists
from urllib2 import urlopen

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool, NullPool

__all__ = [
    'Database',
]


lock = Lock()


class SerializableBase(object):
    """
    This is used as a base class for our declarative Bases.  It allows us to jsonify
    instances of SQLAlchemy models more easily.
    """

    def _asdict(self):
        """ simplejson (used by flask.jsonify) looks for a method with this name """
        return {c.name : getattr(self, c.name) for c in self.__table__.columns}


def get_host_projects(host_id):
    cluster_url_fmt = 'https://noc.wikimedia.org/conf/s{0}.dblist'
    url = cluster_url_fmt.format(host_id)
    projects = urlopen(url).read().splitlines()
    return (host_id, projects)


def get_host_projects_map():
    project_host_map = {}
    # TODO: these numbers are hardcoded, is that ok?
    num_hosts = 7
    host_projects = map(get_host_projects, range(1, num_hosts + 1))
    host_fmt = 's{0}'
    for host_id, projects in host_projects:
        host = host_fmt.format(host_id)
        for project in projects:
            project_host_map[project] = host
    return project_host_map


class Database(object):
    """
    Basically a collection of all database related objects and methods.
    Instantiated after configuration is done, in the wikimetrics.configurables module.
    You should not instantiate this yourself, just do `from .configurables import db`
    """

    def __init__(self, config):
        """
        Initializes the declarative bases that are used throughout the project.
        Initializes the empty engines and sessionmakers that support
        `get_session`, `get_mw_session` and `get_ca_session`.
        """

        self.config = config

        self.WikimetricsBase = declarative_base(cls=SerializableBase)
        self.MediawikiBase = declarative_base(cls=SerializableBase)
        self.CentralAuthBase = declarative_base(cls=SerializableBase)

        self.wikimetrics_engine = None
        self.wikimetrics_sessionmaker = None
        self.wikimetrics_session = None

        self.mediawiki_engines = {}
        self.mediawiki_sessions = {}

        self.centralauth_engine = None
        self.centralauth_sessionmaker = None
        self.centralauth_session = None

        # we instantiate project_host_map lazily
        self._project_host_map = None

    def get_engine(self):
        """
        Create a sqlalchemy engine for the wikimetrics database.

        Returns:
            new or cached sqlalchemy engine connected to the wikimetrics database.
        """
        if self.wikimetrics_engine is None:
            # If changing the parameters to create_engine below, be
            # sure to also reflect them in
            # database_migrations/env.py's create_engine.
            self.wikimetrics_engine = create_engine(
                self.config['WIKIMETRICS_ENGINE_URL'],
                echo=self.config['SQL_ECHO'],
                connect_args={"charset" : "utf8"},
                pool_size=self.config['WIKIMETRICS_POOL_SIZE'],
            )

        return self.wikimetrics_engine

    def get_session(self):
        """
        On the first run, instantiates the Wikimetrics session maker
        and create wikimetrics tables if they don't exist.
        On subsequent runs, it does not re-define the session maker or engine.

        Returns:
            new sqlalchemy session open to the wikimetrics database
        """
        if self.wikimetrics_sessionmaker is None:
            self.get_engine()
            # This import is necessary here so that
            # WikimetricsBase knows about all its children.
            import wikimetrics.models
            self.wikimetrics_sessionmaker = sessionmaker(
                self.wikimetrics_engine,
                expire_on_commit=False,
            )

        if self.wikimetrics_session is None:
            self.wikimetrics_session = scoped_session(self.wikimetrics_sessionmaker)

        # an unhandled exception would leave the session in a bad state, roll it back:
        if not self.wikimetrics_session.is_active:
            self.wikimetrics_session.rollback()
        return self.wikimetrics_session

    def get_mw_session(self, project):
        """
        Based on the mediawiki project passed in, create a sqlalchemy session.

        Parameters:
            project : string name of the mediawiki project (for example: wiki, arwiki)

        Returns:
            new sqlalchemy session connected to the appropriate database.  This method
            caches sqlalchemy session makers and creates sessions from those.
        """
        if project not in self.mediawiki_sessions:
            import wikimetrics.models.mediawiki
            engine = self.get_mw_engine(project)
            if self.config['DEBUG']:
                self.MediawikiBase.metadata.create_all(
                    engine,
                    checkfirst=True
                )

            self.mediawiki_sessions[project] = scoped_session(sessionmaker(engine))

        # an unhandled exception would leave the session in a bad state, roll it back:
        if not self.mediawiki_sessions[project].is_active:
            self.mediawiki_sessions[project].rollback()
        return self.mediawiki_sessions[project]

    def get_mw_engine(self, project):
        """
        Based on the mediawiki project passed in, create a sqlalchemy engine.

        Parameters:
            project : string name of the mediawiki project (for example: wiki, arwiki)

        Returns:
            new or cached sqlalchemy engine connected to the appropriate database.
        """
        if project not in self.mediawiki_engines:
            engine_template = self.config['MEDIAWIKI_ENGINE_URL_TEMPLATE']

            self.mediawiki_engines[project] = create_engine(
                engine_template.format(project),
                echo=self.config['SQL_ECHO'],
                convert_unicode=True,
                # because we are hitting 900 projects in parallel at the same time,
                # pooling does not work as we exhaust our allowed connections for the
                # labsdb user.  This is because we connect with database-specific URIs
                # TODO: connect to all mediawiki databases with one generic URI and
                #       re-enable pooling
                # NOTE: when doing this, don't use s4.labsdb as quarry has dibs :)
                poolclass=NullPool,
            )

        return self.mediawiki_engines[project]

    def get_ca_session(self):
        """
        On the first run, instantiates the centralauth session maker.
        On subsequent runs, it does not re-define the session maker or engine.

        Returns:
            new sqlalchemy session open to the centralauth database
        """
        if self.centralauth_sessionmaker is None:
            # This import is necessary here so that
            # CentralAuthBase knows about all its children.
            import wikimetrics.models.centralauth
            engine = self.get_ca_engine()
            if self.config['DEBUG']:
                self.CentralAuthBase.metadata.create_all(
                    engine,
                    checkfirst=True
                )
            self.centralauth_sessionmaker = sessionmaker(
                self.centralauth_engine,
                expire_on_commit=False,
            )

        if self.centralauth_session is None:
            self.centralauth_session = scoped_session(
                self.centralauth_sessionmaker
            )

        # an unhandled exception would leave the session
        # in a bad state, roll it back:
        if not self.centralauth_session.is_active:
            self.centralauth_session.rollback()
        return self.centralauth_session

    def get_ca_engine(self):
        """
        Create a sqlalchemy engine for the centralauth database.

        Returns:
            new or cached sqlalchemy engine connected to the centralauth database.
        """
        if self.centralauth_engine is None:
            self.centralauth_engine = create_engine(
                self.config['CENTRALAUTH_ENGINE_URL'],
                echo=self.config['SQL_ECHO'],
                convert_unicode=True,
                poolclass=NullPool,
            )
        return self.centralauth_engine

    def get_project_host_map(self, usecache=True):
        """
        Retrieves the list of mediawiki projects from noc.wikimedia.org.
        If we are on development or testing project_host_map
        does not access the network to verify project names.
        Project names are hardcoded.

        Note that the project_host_map_list is fetched
        not at the time we construct the object
        but the first time we request it

        Parameters:
            usecache    : defaults to True and uses a local cache if available

        """
        with lock:
            if self._project_host_map is None or usecache is False:
                project_host_map = {}

                if self.config.get('DEBUG'):
                    # tests/__init__.py overrides this setting if needed
                    for p in self.config.get('PROJECT_HOST_NAMES'):
                        project_host_map[p] = 'localhost'
                else:
                    cache_name = 'project_host_map.json'
                    if not exists(cache_name) or not usecache:
                        project_host_map = get_host_projects_map()
                        if usecache and os.access(cache_name, os.W_OK):
                            try:
                                json.dump(project_host_map, open(cache_name, 'w'))
                            except:
                                print('No rights to write {0}'.format(
                                    os.path.abspath(cache_name)
                                ))
                    elif os.access(cache_name, os.R_OK):
                        project_host_map = json.load(open(cache_name))
                    else:
                        raise Exception('Project host map could not be fetched or read')

                self._project_host_map = project_host_map
            return self._project_host_map


@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """
    Pings the connection on checkout, making sure that it hasn't gone stale.
    This prevents error (OperationalError) (2006, 'MySQL server has gone away').
    This fix can be tested with tests/manual/connection_survives_server_restart.py
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    finally:
        cursor.close()
