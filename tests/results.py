#!/usr/bin/python

from buildservice import BuildService
bs = BuildService(apiurl='https://api.meego.com', config='/etc/boss/oscrc' )
print bs.getRepoState('Trunk')
