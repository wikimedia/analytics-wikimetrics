#!/usr/bin/python
# follow the frog

from setuptools import setup
from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt')

# reqs is a list of requirement
# e.g. ['flask==0.9', 'sqlalchemye==0.8.1']
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='wikimetrics',
    version='0.0.1',
    description='Wikipedia Cohort Analysis Tool',
    url='http://www.github.com/wikimedia/analytics-wikimetrics',
    author='Andrew Otto, Dan Andreescu, Evan Rosen, Stefan Petrea',
    packages=[
        'wikimetrics',
    ],
    install_requires=reqs,
    entry_points={
        'console_scripts': [
            'wikimetrics = wikimetrics.run:main'
        ]
    },
)
