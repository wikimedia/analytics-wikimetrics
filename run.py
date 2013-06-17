#!/usr/bin/python
# TODO: because python 2.* is annoying, talk to ops about python 3

import pprint
import argparse


from wikimetrics.web import app
from wikimetrics.database import db


def web():
    """
    Currently does nothing.
    """
    pass


def test():
    pass


def celery():
    pass


if __name__ == '__main__':
    arg
    config_file = 'config'
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    app.config.from_object(config_file)
    db.config_from_object(config_file)
    
    db.init_db()
    app.run()
    
    main()
    
    parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('integers', metavar='N', type=int, nargs='+',
                   help='an integer for the accumulator')
parser.add_argument('--sum', dest='accumulate', action='store_const',
                   const=sum, default=max,
                   help='sum the integers (default: find the max)')

args = parser.parse_args()
print args.accumulate(args.integers)
