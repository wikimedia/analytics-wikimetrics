import pprint
import logging
import argparse
import nose


logger = logging.getLogger(__name__)


__all__ = [
    'db',
    'queue',
    'app',
]


root_path = ''


def config_web(args):
    from flask import Flask
    
    global app
    app = Flask('wikimetrics')
    app.config.from_pyfile(args.web_config)
    if args.override_config:
        app.config.from_pyfile(args.override_config)
    
    # set the root_path so it can be shared with Database
    # which uses the same config - flask.config.Config
    root_path = app.config.root_path


def config_db(args):
    from wikimetrics.database import Database
    
    global db
    db = Database()
    db.config.from_pyfile(args.db_config)
    if args.override_config:
        db.config.from_pyfile(args.override_config)


def config_celery(args):
    # TODO: move this into wikimetrics without breaking celery
    from celery import Celery
    
    global queue
    # create and configure celery app
    queue = Celery('wikimetrics', include=['wikimetrics'])
    queue.config_from_object(args.celery_config)
    if args.override_config:
        queue.config_from_object(args.override_config)


def web(args):
    config_db(args)
    config_web(args)
    
    app.run()


def test(args):
    config_db(args)
    config_web(args)
    config_celery(args)
    
    nose.run()


def celery(args):
    config_db(args)
    config_celery(args)
    
    from wikimetrics.models import ConcatMetricsJob
    from wikimetrics.models import MultiProjectMetricJob
    from wikimetrics.models import MetricJob
    queue.start()


parser = argparse.ArgumentParser('wikimetrics',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument('--override-config', '-o',
    default = None,
    help='override config file',
    dest='override_config',
)
subparsers = parser.add_subparsers(
    dest='subparser_name',
    title='subcommands',
)

test_parser = subparsers.add_parser('test', help='runs nosetests')
test_parser.set_defaults(func=test)
test_parser.add_argument('--web-config', '-w',
    default='config/web_config.py',
    help='Flask config file',
    dest='web_config',
)
test_parser.add_argument('--db-config', '-d',
    default='config/db_config.py',
    help='Database config file',
    dest='db_config',
)

web_parser = subparsers.add_parser('web', help='runs flask webserver')
web_parser.set_defaults(func=web)
web_parser.add_argument('--web-config', '-w',
    default='config/web_config.py',
    help='Flask config file',
    dest='web_config',
)
web_parser.add_argument('--db-config', '-d',
    default='config/db_config.py',
    help='Database config file',
    dest='db_config',
)

celery_parser = subparsers.add_parser('celery', help='runs celery broker and workers')
celery_parser.set_defaults(func=celery)
celery_parser.add_argument('--celery-config', '-c',
    default='config/celery_config.py',
    help='Celery config file',
    dest='celery_config',
)

args = parser.parse_args()
logger.info('running with arguments:\n%s', pprint.pformat(vars(args)))
args.func(args)


import controllers

login_manager = LoginManager()
login_manager.init_app(app)

oauth = OAuth()
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
