from __future__ import with_statement
from copy import deepcopy
from os import environ, path
from alembic import context
from sqlalchemy import engine_from_config, pool, create_engine
from logging.config import fileConfig

# try to link puppet config files to be used by wikimetrics
# this has to be done before importing any module from it
# if file does not exist, default local file will be used
db_config_file = '/etc/wikimetrics/db_config.yaml'
queue_config_file = '/etc/wikimetrics/queue_config.yaml'
if path.isfile(db_config_file):
    environ['WIKIMETRICS_DB_CONFIG'] = db_config_file
if path.isfile(queue_config_file):
    environ['WIKIMETRICS_QUEUE_CONFIG'] = queue_config_file

from wikimetrics.configurables import db, setup_testing_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers
fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
# initialize metadata
#db.get_session()
# set metadata
target_metadata = db.WikimetricsBase.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_engine(config, url_field='WIKIMETRICS_ENGINE_URL'):
    """
    Create a sqlalchemy engine for a database.

    Returns:
        sqlalchemy engine connected to the database.
    """

    return create_engine(
        config[url_field],
        echo=config['SQL_ECHO'],
        connect_args={"charset" : "utf8"},
        pool_size=config['WIKIMETRICS_POOL_SIZE'],
    )


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = db.get_engine().url
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Runs for wikimetrics, wikimetrics_testing
    and centralauth_testing databases.

    """
    config = db.config
    engine = get_engine(config)
    migrations = [(engine, target_metadata)]

    if db.config['DEBUG'] is True:
        test_config = setup_testing_config(deepcopy(config))
        # add wikimetrics_testing migrations
        test_engine = get_engine(test_config)
        test_metadata = db.WikimetricsBase.metadata
        migrations.append((test_engine, test_metadata))
        # NOTE: centralauth and mediawiki schemas should be maintained
        # manually and not managed with alembic, as they are not schemas
        # we own

    for eng, meta_data in migrations:
        connection = eng.connect()
        context.configure(connection=connection, target_metadata=meta_data)

        print("Running migration for " + eng.url.database)
        try:
            with context.begin_transaction():
                context.run_migrations()
        finally:
            connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
