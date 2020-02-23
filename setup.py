#!/usr/bin/python2
from setuptools import setup

version = open('VERSION').read().strip()

setup(
    name='buildservice',
    version=version,
    description='Module to access OBS server',
    url='https://github.com/MeeGoIntegration/python-buildservice',
    packages=['buildservice'],
    install_requires=['osc<0.140'],
    python_requires='>=2.7,<3.0',
)
