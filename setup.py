#!/usr/bin/env python3
from setuptools import setup

version = open('VERSION').read().strip()

setup(
    name='buildservice',
    version=version,
    description='Module to access OBS server',
    url='https://github.com/MeeGoIntegration/python-buildservice',
    packages=['buildservice'],
    install_requires=['osc'],
    python_requires='>=3.5',
)
