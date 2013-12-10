
import sys
sys.stdout = sys.stderr     # replace the stdout stream

from os import environ
environ['WIKIMETRICS_DB_CONFIG'] = '/etc/wikimetrics/db_config.yaml'
environ['WIKIMETRICS_WEB_CONFIG'] = '/etc/wikimetrics/web_config.yaml'
environ['WIKIMETRICS_QUEUE_CONFIG'] = '/etc/wikimetrics/queue_config.yaml'

from wikimetrics.configurables import app as application
