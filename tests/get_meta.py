#!/usr/bin/env python3

import settings

print('project meta of '+settings.testprj+':')
print(settings.bs.getProjectMeta(settings.testprj))

print('package meta of '+settings.testprj+'/'+settings.testpkg+':')
print(settings.bs.getPackageMeta(settings.testprj,settings.testpkg))
