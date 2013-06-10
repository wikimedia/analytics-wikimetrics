from config_secret import *

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_RESULT_EXPIRES = 3600
CELERY_DISABLE_RATE_LIMITS = True

DEBUG = True

SQL_ECHO = False
