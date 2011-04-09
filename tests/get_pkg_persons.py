#!/usr/bin/python

from pprint import pprint

from buildservice import BuildService
bs = BuildService(apiurl='http://api.meego.com', oscrc='/etc/boss/oscrc' )

print 'Bugowners of Trunk/bash:'
pprint(bs.getPackagePersons('Trunk', 'bash', 'bugowner'))
print 'Maintainers of Trunk/bash:'
pprint(bs.getPackagePersons('Trunk', 'bash', 'maintainers'))
