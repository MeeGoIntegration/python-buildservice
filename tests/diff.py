#!/usr/bin/env python3

import settings
from osc import conf, core
import urllib2
import random

print("Diffing 10 random packages from "+settings.testprj+" and "+settings.testprj2)
packages = random.sample(settings.bs.getPackageList(settings.testprj),10)
for src_package in packages:
  print("Checking "+src_package)
  try:
    diff = core.server_diff(settings.bs.apiurl,
                      settings.testprj, src_package, None,
                      settings.testprj2, src_package, None, False)
    if not diff:
      print("No difference")
    else:
      print(diff)
  except urllib2.HTTPError as err:
   if err.code == 404:
     print("No "+src_package+" in "+settings.testprj2)
   else:
     raise
