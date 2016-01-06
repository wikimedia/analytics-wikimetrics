"""
Loads dependencies from requirements.txt and specifies installation details
"""
#!/usr/bin/env python
# follow the frog

from setuptools import setup, find_packages
from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects
INSTALL_REQS = parse_requirements('requirements.txt', session=False)

# REQS is a list of requirement
# e.g. ['flask==0.9', 'sqlalchemye==0.8.1']
REQS = [str(ir.req) for ir in INSTALL_REQS]

setup(
    name='wikimetrics',
    version='0.0.1',
    description='Wikipedia Cohort Analysis Tool',
    url='http://www.github.com/wikimedia/analytics-wikimetrics',
    author='Andrew Otto, Dan Andreescu, Evan Rosen, Stefan Petrea',
    packages=find_packages(),
    install_requires=REQS,
    entry_points={
        'console_scripts': [
            'wikimetrics = wikimetrics.run:main'
        ]
    },
)
