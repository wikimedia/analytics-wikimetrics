#!/usr/bin/python

from setuptools import setup

setup(
    name='wikimetrics',
    version='0.0.1',
    description='Wikipedia User Analysis Tool',
    url='http://www.github.com/wikimedia/analytics-wikimetrics',
    author='Dan Andreescu & Evan Rosen',
    author_email='dandreescu@wikimedia.org',

    packages = [
        'wikimetrics',
    ],
    entry_points = {
        'console_scripts': [
            'wikimetrics = wikimetrics.process:main',
        ]
    },
    install_requires=[
       "sqlalchemy == 0.8.1",
       "flask == 0.9",
   ],
)
