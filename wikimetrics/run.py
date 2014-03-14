#!/usr/bin/env python
import argparse
import sys
import logging
import pprint
from os import environ as env
from .configurables import config_web, config_db, config_queue
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


def run_queue():
    from configurables import queue
    from wikimetrics.schedules import daily
    queue.start(argv=['celery', 'worker', '-l', queue.conf['LOG_LEVEL']])


def run_scheduler():
    from configurables import queue
    queue.start(argv=[
        'celery', 'beat',
        '-s', queue.conf['CELERY_BEAT_DATAFILE'],
        '--pidfile', queue.conf['CELERY_BEAT_PIDFILE'],
    ])


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
            'queue',
            'scheduler',
        ],
        # NOTE: flake made me format the strings this way, nothing could be uglier
        help='''
            web       : runs flask webserver...
            test      : run nosetests...
            queue     : runs celery worker...
            scheduler : runs celery beat scheduler...
            import    : configures everything and runs nothing...
        ''',
    )
    # get defaults from environment variables
    web_config = 'wikimetrics/config/web_config.yaml'
    if 'WIKIMETRICS_WEB_CONFIG' in env:
        web_config = env['WIKIMETRICS_WEB_CONFIG']
    db_config = 'wikimetrics/config/db_config.yaml'
    if 'WIKIMETRICS_DB_CONFIG' in env:
        db_config = env['WIKIMETRICS_DB_CONFIG']
    queue_config = 'wikimetrics/config/queue_config.yaml'
    if 'WIKIMETRICS_QUEUE_CONFIG' in env:
        queue_config = env['WIKIMETRICS_QUEUE_CONFIG']
    
    # add parser arguments with those defaults
    parser.add_argument(
        '--web-config', '-w',
        default=web_config,
        help='Flask config file',
        dest='web_config',
    )
    parser.add_argument(
        '--db-config', '-d',
        default=db_config,
        help='Database config file',
        dest='db_config',
    )
    parser.add_argument(
        '--queue-config', '-c',
        default=queue_config,
        help='Celery config file',
        dest='queue_config',
    )
    return parser


##################################
# This runs at import time to prepare
# wikimetrics.configurables
##################################
parser = setup_parser()
args, others = parser.parse_known_args()
logger.info('running with arguments:\n%s', pprint.pformat(vars(args)))

# runs the appropriate config function (web, queue, test)
config_web(args)
config_db(args)
config_queue(args)


def main():
    # runs the appropriate run function
    if args.mode == 'web':
        run_web()
    elif args.mode == 'test':
        run_test()
    elif args.mode == 'queue':
        run_queue()
    elif args.mode == 'scheduler':
        run_scheduler()
    elif args.mode == 'import':
        pass


if __name__ == '__main__':
    main()
