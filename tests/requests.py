#!/usr/bin/env python3

import settings
from pprint import pprint

user = settings.bs.getUserName()
print('Your username seems to be '+user)
print('Creating a request for deleting '+settings.testprj+'/'+settings.testpkg)
options=[{'action': 'delete','tgt_project': settings.testprj,'tgt_package': settings.testpkg}]
request = settings.bs.createRequest(options,'Description','Comment',True)
print('Adding a review to previous created request with ID: '+request.reqid)
if not settings.bs.addReview(request.reqid,"Message",user):
  print("Failed!")
  exit()
print('Accepting the review')
if not settings.bs.setReviewState(request.reqid,"accepted","Message2",user):
  print("Failed!")
  exit()
print('Revoking the request')
if not settings.bs.setRequestState(request.reqid,"revoked","Message3"):
  print("Failed!")
  exit()
