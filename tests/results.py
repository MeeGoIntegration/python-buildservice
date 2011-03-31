#!/usr/bin/python

from buildservice import BuildService
bs = BuildService(apiurl = 'http://api.meego.com', oscrc = "/etc/oscrc")
print bs.getRepoState('Trunk')
