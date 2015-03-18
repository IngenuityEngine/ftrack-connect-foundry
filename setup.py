# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import re

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

ROOT_PATH = os.path.dirname(
    os.path.realpath(__file__)
)

SOURCE_PATH = os.path.join(
    ROOT_PATH, 'source'
)

RESOURCE_PATH = os.path.join(
    ROOT_PATH, 'resource'
)

README_PATH = os.path.join(ROOT_PATH, 'README.rst')


class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest
        raise SystemExit(pytest.main(self.test_args))


setup(
    name='ftrack-connect-foundry',
    version='0.1.0',
    description='ftrack integration with The Foundry API.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, integration, connect, the foundry',
    url='https://bitbucket.org/ftrack/ftrack-connect-foundry',
    author='ftrack',
    author_email='support@ftrack.com',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 1'
    ],
    install_requires=[
        'ftrack-connect >= 0.1, < 1'
    ],
    tests_require=['pytest >= 2.3.5'],
    cmdclass={
        'test': PyTest
    },
    dependency_links=[
        ('https://bitbucket.org/ftrack/ftrack-connect/get/0.1.9.zip'
        '#egg=ftrack-connect-0.1.9'),
        ('https://bitbucket.org/ftrack/lowdown/get/0.1.0.zip'
         '#egg=lowdown-0.1.0')
    ]
)
