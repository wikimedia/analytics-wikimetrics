#!/usr/bin/python
# TODO: because python 2.* is annoying, talk to ops about python 3

import pprint
import logging
import argparse
import nose

from wikimetrics.web import app
from wikimetrics.database import db


logger = logging.getLogger(__name__)


def config_web(args):
    app.config.from_object(args.web_config)
    app.config.from_object(args.override_config)


def config_db(args):
    db.config.from_object(args.db_config)
    db.config.from_object(args.override_config)


def config_celery(args):
    celery.config_from_object(args.celery_config)
    celery.config_from_object(args.override_config)


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
    
    celery.start()


def parse_args():
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


def main():
    parse_args() 


if __name__ == '__main__':
    main()
