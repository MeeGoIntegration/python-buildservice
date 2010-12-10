#!/usr/bin/python

from buildservice import BuildService
bs = BuildService('http://api.meego.com')
print bs.getRepoState('Trunk')
