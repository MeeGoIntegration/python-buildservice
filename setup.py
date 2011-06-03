#!/usr/bin/python2
from distutils.core import setup
import os, sys

static_files=[]
static_files.append((os.path.join('/etc','boss'), ['conf/oscrc']))

# For debian based systems, '--install-layout=deb' is needed after 2.6
if sys.version_info[:2] <= (2, 5) and '--install-layout=deb' in sys.argv:
    del sys.argv[sys.argv.index('--install-layout=deb')]

version_path = 'VERSION'
try:
    # first line should be the version number
    version = open(version_path).readline().strip()
except IOError:
    print 'WARNING: Cannot write version number file'
    pass

setup(name = 'buildservice',
      version = version,
      description = 'Module to access OBS server',
      author = 'Anas Nashif',
      author_email = 'anas.nashif@intel.com',
      url = 'http://meego.gitorious.org/meego-infrastructure-tools/python-buildservice',
      packages = ['buildservice'],
      data_files = static_files,
)
