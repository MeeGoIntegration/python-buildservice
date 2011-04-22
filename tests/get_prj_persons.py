#!/usr/bin/python

from pprint import pprint

from buildservice import BuildService
bs = BuildService(apiurl='http://api.meego.com', oscrc='/etc/boss/oscrc' )

print 'Bugowners of Trunk'
pprint(bs.getProjectPersons('Trunk', 'bugowner'))
print 'Maintainers of Trunk:'
pprint(bs.getProjectPersons('Trunk', 'maintainers'))
