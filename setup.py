#!/usr/bin/python2
from distutils.core import setup
import os, sys

setup(name = 'buildservice',
  version = '0.1',
  description = 'access build service data',
  author = 'Anas Nashif',
  author_email = 'anas.nashif@intel.com',
  url = 'http://meego.gitorious.org/meego-infrastructure-tools/python-buildservice',
  packages = ['buildservice'],
)
