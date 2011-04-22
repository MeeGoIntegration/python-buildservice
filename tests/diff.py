#!/usr/bin/python

from buildservice import BuildService
from osc import conf, core
bs = BuildService(apiurl = 'https://api.meego.com', oscrc = "/etc/oscrc")
#print bs.getRepoState('Trunk')
#print bs.getProjectDiff('Trunk:Testing', 'Trunk')

packages = bs.getPackageList('Trunk:Testing')
for src_package in packages:
  print src_package
  diff = core.server_diff(bs.apiurl,
                      'Trunk', src_package, None,
                      'Trunk:Testing', src_package, None, False)
  p = open(src_package, 'w')
  p.write(diff)
  p.close()
