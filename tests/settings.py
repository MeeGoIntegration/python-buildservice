#!/usr/bin/env python3

from buildservice import BuildService
from os.path import expanduser
import os

home = expanduser("~")
apiurl = os.environ.get('OBSAPI')
oscrc = os.environ.get('OSCRC', home+"/.config/osc/oscrc")
testprj = os.environ.get('OBSTESTPRJ')
testprj2 = os.environ.get('OBSTESTPRJ2')
testpkg = os.environ.get('OBSTESTPKG')
testfile = os.environ.get('OBSTESTFILE')
if not apiurl:
        raise ValueError('You must have "OBSAPI" variable')
if not oscrc:
        raise ValueError('You must have "OSCRC" variable')
if not testprj:
        raise ValueError('You must have "OBSTESTPRJ" variable')
if not testprj2:
        raise ValueError('You must have "OBSTESTPRJ2" variable')
if not testpkg:
        raise ValueError('You must have "OBSTESTPKG" variable')
if not testfile:
        raise ValueError('You must have "OBSTESTFILE" variable')

bs = BuildService(apiurl,oscrc)

print("**********************************")
print("Our test settings:")
print("API: "+apiurl)
print("OSCRC: "+oscrc)
print("Test project 1: "+testprj)
print("Test project 2: "+testprj2)
print("Test package: "+testpkg)
print("Test file: "+testfile)
print("**********************************")
