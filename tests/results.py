#!/usr/bin/python

import settings
from pprint import pprint

print "Repository state of "+settings.testprj
pprint(settings.bs.getRepoState(settings.testprj))
