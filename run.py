#!/usr/bin/python
# TODO: because python 2.* is annoying, talk to ops about python 3

import pprint

from wikimetrics.web import app
from wikimetrics.database import init_db

def main():
    pass

if __name__ == '__main__':
    init_db()
    app.run()
    
    main()
