#!/usr/bin/python
from configurables import app, queue
import nose


##################################
# global parser setup and options
##################################
parser = argparse.ArgumentParser('wikimetrics',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument('--override-config', '-o',
    default = None,
    help='override config file',
    dest='override_config',
)
#parser.add_argument('func', default=lambda : None)
subparsers = parser.add_subparsers(
    dest='command',
    title='subcommands',
)


##################################
# TEST subparser setup and options
##################################
def test(args):
    config_web(args)
    config_db(args)
    config_celery(args)
    

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
test_parser.add_argument('--celery-config', '-c',
    default='wikimetrics/config/celery_config.py',
    help='Celery config file',
    dest='celery_config',
)


##################################
# WEB subparser setup and options
##################################
def web(args):
    config_web(args)
    config_db(args)


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


##################################
# CELERY subparser setup and options
##################################
def celery(args):
    config_db(args)
    config_celery(args)
    
    from wikimetrics.models import ConcatMetricsJob
    from wikimetrics.models import MultiProjectMetricJob
    from wikimetrics.models import MetricJob


celery_parser = subparsers.add_parser('celery', help='runs celery broker and workers')
celery_parser.set_defaults(func=celery)
celery_parser.add_argument('--celery-config', '-c',
    default='config/celery_config.py',
    help='Celery config file',
    dest='celery_config',
)
celery_parser.add_argument('--db-config', '-d',
    default='config/db_config.py',
    help='Database config file',
    dest='db_config',
)


##################################
# RUN methods
##################################
def run_web():
    app.run()


def run_test():
    nose.run(module='tests')


def run_celery():
    queue.start()


def main():
    args = parser.parse_args()
    logger.info('running with arguments:\n%s', pprint.pformat(vars(args)))
    
    # runs the appropriate config function (web, celery, test)
    args.func(args)
    
    # runs the appropriate run function
    if args.command == 'web':
        run_web()
    elif args.command == 'test':
        run_test()
    elif args.command == 'celery':
        run_celery()


if __name__ == '__main__':
    main()
