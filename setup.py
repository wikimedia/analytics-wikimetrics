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
        'requests',
        'flask == 0.9',
        'flask-login',
        'flask-oauth',
        'flask-wtf',
        'nose == 1.3.0',
        'coverage == 3.6',
        'celery == 3.0',
        'celery-with-redis',
    ],
    entry_points={
        'console_scripts': [
            'wikimetrics = wikimetrics.run:main'
        ]
    }
)
