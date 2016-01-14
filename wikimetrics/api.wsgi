
import sys
sys.stdout = sys.stderr     # replace the stdout stream

from os import environ
environ['WIKIMETRICS_DB_CONFIG'] = '/srv/wikimetrics/config/db_config.yaml'
environ['WIKIMETRICS_WEB_CONFIG'] = '/srv/wikimetrics/config/web_config.yaml'
environ['WIKIMETRICS_QUEUE_CONFIG'] = '/srv/wikimetrics/config/queue_config.yaml'

from wikimetrics.configurables import app as application
