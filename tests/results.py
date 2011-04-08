#!/usr/bin/python

from buildservice import BuildService
bs = BuildService(apiurl='http://api.meego.com', config='/etc/boss/oscrc' )
print bs.getRepoState('Trunk')
