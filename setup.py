#!/usr/bin/python2
from distutils.core import setup
import os, sys

static_files=[]
static_files.append((os.path.join('/etc','boss'), ['conf/build-service.conf']))

setup(name = 'buildservice',
             version = '0.2',
             description = 'access build service data',
             author = 'Anas Nashif',
             author_email = 'anas.nashif@intel.com',
             url = 'http://meego.gitorious.org/meego-infrastructure-tools/python-buildservice',
             packages = ['buildservice'],
             data_files = static_files,
)
