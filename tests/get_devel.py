#!/usr/bin/python

from pprint import pprint

from buildservice import BuildService
bs = BuildService(apiurl='http://api.meego.com', oscrc='/etc/boss/oscrc' )

print 'devel project of Trunk:'
pprint(bs.getProjectDevel('Trunk'))

print 'devel package of Trunk/bash:'
pprint(bs.getPackageDevel('Trunk', 'bash'))
