#!/usr/bin/python

from setuptools import setup

setup(
    name='wikimetrics',
    version='0.0.1',
    description='Wikipedia User Analysis Tool',
    url='http://www.github.com/wikimedia/analytics-wikimetrics',
    author='Andrew Otto, Dan Andreescu, Evan Rosen',
    packages=[
        'wikimetrics',
    ],
    install_requires=[
        'sqlalchemy == 0.8.1',
        'mysql-python == 1.2.3',
        'requests == 1.2.3',
        'flask == 0.9',
        'flask-login == 0.2.4',
        'flask-oauth == 0.12',
        'wtforms == 1.0.4',
        # needed to run tests but bad in prod environment
        # because tests are currently distructive 'nose == 1.3.0',
        'coverage == 3.6',
        'celery == 3.0',
        'celery-with-redis == 3.0',
    ],
    entry_points={
        'console_scripts': [
            'wikimetrics = wikimetrics.run:main'
        ]
    }
)
