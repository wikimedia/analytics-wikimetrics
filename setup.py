#!/usr/bin/python

from setuptools import setup

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
       "coverage == 3.6",
       "celery == 3.0",
       "celery-with-redis",
   ],
)
