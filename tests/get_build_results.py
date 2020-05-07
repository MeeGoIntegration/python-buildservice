#!/usr/bin/env python3

import settings
from pprint import pprint

print('Checking project '+settings.testprj+':')
for repo in settings.bs.getProjectRepositories(settings.testprj):
  print('  Checking repo '+repo+':')
  print('    Archs:')
  pprint(settings.bs.getRepositoryArchs(settings.testprj, repo))
  print('    Results:')
  pprint(settings.bs.getRepoResults(settings.testprj, repo))
