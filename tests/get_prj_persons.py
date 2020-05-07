#!/usr/bin/env python3

import settings

print('Bugowners of '+settings.testprj2)
print(settings.bs.getProjectPersons(settings.testprj2, 'bugowner'))
print('Maintainers of '+settings.testprj)
print(settings.bs.getProjectPersons(settings.testprj, 'maintainer'))
