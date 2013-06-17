#!/usr/bin/python
# TODO: because python 2.* is annoying, talk to ops about python 3

import pprint
import logging
import argparse

#from wikimetrics.web import app
#from wikimetrics.database import db


logger = logging.getLogger(__name__)

def web(args):
    #app.config.from_object(args.web_config)
    #db.config_from_object(args.db_config)
    
    
    #db.init_db()
    #app.run()
    pass


def test(args):
    pass


def celery(args):
    pass


def parse_args():
    parser = argparse.ArgumentParser('wikimetrics',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config',
            default = None,
            help='override config file')    
    subparsers = parser.add_subparsers(
            dest='subparser_name',
            title='subcommands')
    
    test_parser = subparsers.add_parser('test', help='runs nosetests')
    test_parser.set_defaults(func=test)
    test_parser.add_argument('--web-config',
            default='config/web_config.py',
            help='Flask config file')
    test_parser.add_argument('--db-config',
            default='config/db_config.py',
            help='Database config file')
    
    web_parser = subparsers.add_parser('web', help='runs flask webserver')
    web_parser.set_defaults(func=web)
    web_parser.add_argument('--web-config',
            default='config/web_config.py',
            help='Flask config file')
    web_parser.add_argument('--db-config',
            default='config/db_config.py',
            help='Database config file')
    
    celery_parser = subparsers.add_parser('celery', help='runs celery broker and workers')
    celery_parser.set_defaults(func=celery)
    celery_parser.add_argument('--celery-config',
            default='config/celery_config.py',
            help='Celery config file')
    
    args = parser.parse_args()
    logger.info('running with arguments:\n%s', pprint.pformat(vars(args)))
    args.func(args)


def main():
    parse_args() 


if __name__ == '__main__':
    main()
