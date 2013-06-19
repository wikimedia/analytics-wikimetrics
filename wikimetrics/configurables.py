import pprint
import logging
import argparse
import sys
import os


logger = logging.getLogger(__name__)


__all__ = [
    'db',
    'queue',
    'app',
    'login_manager',
    'google',
    'args'
]


root_path = ''


def create_object_from_config_file(path):
    dir, fname = os.path.split(path)
    sys.path.insert(0, os.path.expanduser(dir))
    return __import__(dir.replace('/','.') + '.' + os.path.splitext(fname)[0])


def config_web(args):
    from flask import Flask
    from flask.ext.login import LoginManager
    from flask.ext.oauth import OAuth
    
    global app
    app = Flask('wikimetrics')
    app.config.from_pyfile(args.web_config)
    if args.override_config:
        app.config.from_pyfile(args.override_config)
    
    # set the root_path so it can be shared with Database
    # which uses the same config - flask.config.Config
    global root_path
    root_path = app.config.root_path
    
    global login_manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    oauth = OAuth()
    global google
    google = oauth.remote_app(
        'google',
        base_url=app.config['GOOGLE_BASE_URL'],
        authorize_url=app.config['GOOGLE_AUTH_URI'],
        request_token_url=None,
        request_token_params={
            'scope': app.config['GOOGLE_AUTH_SCOPE'],
            'response_type': 'code',
        },
        access_token_url=app.config['GOOGLE_TOKEN_URI'],
        access_token_method='POST',
        access_token_params={
            'grant_type':
            'authorization_code'
        },
        consumer_key=app.config['GOOGLE_CLIENT_ID'],
        consumer_secret=app.config['GOOGLE_CLIENT_SECRET'],
    )


def config_db(args):
    from wikimetrics.database import Database
    
    global db
    db = Database()
    db.config.root_path = root_path
    db.config.from_pyfile(args.db_config)
    if args.override_config:
        db.config.from_pyfile(args.override_config)


def config_celery(args):
    # TODO: move this into wikimetrics without breaking celery
    from celery import Celery
    
    global queue
    # create and configure celery app
    queue = Celery('wikimetrics', include=['wikimetrics'])
    config_object = create_object_from_config_file(args.celery_config)
    queue.config_from_object(config_object)
    if args.override_config:
        queue.config_from_object(args.override_config)






