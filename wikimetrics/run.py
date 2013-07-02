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
    app.run()


def run_test():
    import nose
    nose.run(module='tests')


def run_celery():
    from configurables import queue
    from .models import ConcatMetricsJob
    from .models import MultiProjectMetricJob
    from .models import MetricJob
    queue.start(argv=['celery', 'worker', '-l', 'DEBUG'])


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
        'mode',
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
        default='config/web_config.py',
        help='Flask config file',
        dest='web_config',
    )
    parser.add_argument(
        '--db-config', '-d',
        default='wikimetrics/config/db_config.py',
        help='Database config file',
        dest='db_config',
    )
    parser.add_argument(
        '--celery-config', '-c',
        default='wikimetrics/config/celery_config.py',
        help='Celery config file',
        dest='celery_config',
    )
    return parser


##################################
# This runs at import time to prepare
# wikimetrics.configurables
##################################
parser = setup_parser()
args = parser.parse_args()
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
