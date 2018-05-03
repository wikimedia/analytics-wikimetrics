"""
Loads dependencies from requirements.txt and specifies installation details
"""
#!/usr/bin/env python
# follow the frog

from setuptools import setup, find_packages


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


INSTALL_REQS = parse_requirements('requirements.txt')

setup(
    name='wikimetrics',
    version='0.0.1',
    description='Wikipedia Cohort Analysis Tool',
    url='http://www.github.com/wikimedia/analytics-wikimetrics',
    author='Andrew Otto,Dan Andreescu,Evan Rosen,Marcel Ruiz,Nuria Ruiz,Stefan Petrea',
    packages=find_packages(),
    install_requires=INSTALL_REQS,
    entry_points={
        'console_scripts': [
            'wikimetrics = wikimetrics.run:main'
        ]
    },
)
