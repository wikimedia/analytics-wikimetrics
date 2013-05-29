#!/usr/bin/python

from setuptools import setup
from celery import Celery

setup(
    name='wikimetrics',
    version='0.0.1',
    description='Wikipedia User Analysis Tool',
    url='http://www.github.com/wikimedia/analytics-wikimetrics',
    author='Andrew Otto, Dan Andreescu, Evan Rosen',

    packages = [
        'wikimetrics',
    ],
    install_requires=[
       "sqlalchemy == 0.8.1",
       "flask == 0.9",
       "nose == 1.3.0",
       "celery == 3.0",
       "celery-with-redis",
   ],
)


class Configuration(object):
    # celery configuration
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_TASK_RESULT_EXPIRES=3600
    CELERY_DISABLE_RATE_LIMITS = True

celery = Celery('wikimetrics', include=['wikimetrics'])
celery.config_from_object(Configuration)
