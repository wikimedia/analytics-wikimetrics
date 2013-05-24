#!/usr/bin/python

from setuptools import setup

setup(
    name='user_metrics',
    version='0.0.1',
    description='Wikipedia User Analysis Tool',
    url='http://www.github.com/wikimedia/analytics-user-metrics',
    author='Dan Andreescu & Evan Rosen',
    author_email='dandreescu@wikimedia.org',

    packages = [
        'user_metrics',
        'user_metrics.api',
    ],
    entry_points = {
        'console_scripts': [
            'userstats = userstats.process:main',
        ]
    },
    install_requires=[
       "sqlalchemy == 0.8.1",
       "flask == 0.9",
   ],
)
