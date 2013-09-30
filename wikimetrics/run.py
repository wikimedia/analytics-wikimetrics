#!/usr/bin/python
import argparse
import sys
import logging
import pprint
from .configurables import config_web, config_db, config_celery
logger = logging.getLogger(__name__)


##################################
# RUN methods
##################################
def run_web():
    from configurables import app
    app.run(host=app.config.get('SERVER_HOST'), port=app.config.get('SERVER_PORT'))


def run_test():
    import nose
    nose.run(module='tests')


def run_celery():
    from configurables import queue
    queue.start(argv=['celery', 'worker', '-l', queue.conf['LOG_LEVEL']])


def setup_parser():
    parser = argparse.ArgumentParser(
        'wikimetrics',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--override-config', '-o',
        default=None,
        help='override config file',
        dest='override_config',
    )
    parser.add_argument(
        '--mode',
        nargs='?',
        default='import',
        choices=[
            'import',
            'web',
            'test',
            'celery',
        ],
        # NOTE: flake made me format the strings this way, nothing could be uglier
        help='''
            web    : runs flask webserver...
            test   : run nosetests...
            celery : runs celery worker...
            import : configures everything and runs nothing...
        ''',
    )
    parser.add_argument(
        '--web-config', '-w',
        default='wikimetrics/config/web_config.yaml',
        help='Flask config file',
        dest='web_config',
    )
    parser.add_argument(
        '--db-config', '-d',
        default='wikimetrics/config/db_config.yaml',
        help='Database config file',
        dest='db_config',
    )
    parser.add_argument(
        '--celery-config', '-c',
        default='wikimetrics/config/celery_config.yaml',
        help='Celery config file',
        dest='celery_config',
    )
    return parser


##################################
# This runs at import time to prepare
# wikimetrics.configurables
##################################
parser = setup_parser()
args, others = parser.parse_known_args()
logger.info('running with arguments:\n%s', pprint.pformat(vars(args)))

# runs the appropriate config function (web, celery, test)
config_web(args)
config_db(args)
config_celery(args)


def main():
    # runs the appropriate run function
    if args.mode == 'web':
        run_web()
    elif args.mode == 'test':
        run_test()
    elif args.mode == 'celery':
        run_celery()
    elif args.mode == 'import':
        pass


if __name__ == '__main__':
    main()
