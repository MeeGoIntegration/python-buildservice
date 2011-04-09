#!/usr/bin/python

from buildservice import BuildService
bs = BuildService(apiurl='http://api.meego.com', oscrc='/etc/boss/oscrc' )
print bs.getRepoState('Trunk')
