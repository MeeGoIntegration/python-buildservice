#!/usr/bin/env python3

import settings
from pprint import pprint
import os

print('Checking package list of '+settings.testprj+':')
pprint(settings.bs.getPackageList(settings.testprj))

print('and targets :')
targets = settings.bs.getTargets(settings.testprj)
pprint(targets)

print('Checking status of '+settings.testprj+'/'+settings.testpkg+':')
pprint(settings.bs.getPackageStatus(settings.testprj,settings.testpkg))

print('Checking file list of '+settings.testprj+'/'+settings.testpkg+':')
files = settings.bs.getPackageFileList(settings.testprj,settings.testpkg)
pprint(files)

print('Fetching file '+settings.testprj+'/'+settings.testpkg+'/'+settings.testfile+':')
print(settings.bs.getFile(settings.testprj,settings.testpkg,settings.testfile))

print('Checking binary list of '+settings.testprj+'/'+settings.testpkg+'/'+targets[0]+':')
bins = settings.bs.getBinaryList(settings.testprj,targets[0],settings.testpkg)
pprint(bins)

print('Checking binary info of '+settings.testprj+'/'+settings.testpkg+'/'+targets[0]+'/'+bins[2]+':')
pprint(settings.bs.getBinaryInfo(settings.testprj,targets[0],settings.testpkg,bins[2]))
