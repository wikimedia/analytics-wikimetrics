#!/usr/bin/python
import argparse
import logging
import pprint
from .configurables import config_web, config_db, config_celery
logger = logging.getLogger(__name__)



def config_web_mode(args):
    config_web(args)
    config_db(args)
    config_celery(args)


def config_test_mode(args):
    config_web(args)
    config_db(args)
    config_celery(args)


def config_celery_mode(args):
    config_db(args)
    config_celery(args)


def config_import_only_mode(args):
    config_web(args)
    config_db(args)
    config_celery(args)
    


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
    from wikimetrics.models import ConcatMetricsJob
    from wikimetrics.models import MultiProjectMetricJob
    from wikimetrics.models import MetricJob
    queue.start()

def setup_parser():
    parser = argparse.ArgumentParser('wikimetrics',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--override-config', '-o',
        default = None,
        help='override config file',
        dest='override_config',
    )
    parser.add_argument('mode',
        nargs='?',
        default='import', 
        choices=[
            'import',
            'web',
            'test',
            'celery',
        ],
        help='web    : runs flask webserver'\
            'test   : run nosetests'\
            'celery : runs celery worker'
            'import : configures everything and runs nothing',
    )
    parser.add_argument('--web-config', '-w',
        default='config/web_config.py',
        help='Flask config file',
        dest='web_config',
    )
    parser.add_argument('--db-config', '-d',
        default='config/db_config.py',
        help='Database config file',
        dest='db_config',
    )
    parser.add_argument('--celery-config', '-c',
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
pprint.pprint(vars(args))
logger.info('running with arguments:\n%s', pprint.pformat(vars(args)))

# runs the appropriate config function (web, celery, test)
if args.mode == 'web':
    print 'running config_web_mode'
    config_web_mode(args)
elif args.mode == 'test':
    config_test_mode(args)
elif args.mode == 'celery':
    config_celery_mode(args)
elif args.mode == 'import':
    print 'running config_import_only'
    config_import_only_mode(args)




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
