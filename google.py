#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gflags
import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

import ConfigParser

config = ConfigParser.ConfigParser()
config.read(['config.ini.dist', 'config.ini'])

FLAGS = gflags.FLAGS
FLOW = OAuth2WebServerFlow(
	client_id=config.get('google', 'client_id'),
	client_secret=config.get('google', 'client_secret'),
	scope=config.get('google', 'scope'),
	user_agent='Endomondo Sync/0.1')
    
    
# To disable the local server feature, uncomment the following line:
# FLAGS.auth_local_webserver = False

# If the Credentials don't exist or are invalid, run through the native client
# flow. The Storage object will ensure that if successful the good
# Credentials will get written back to a file.
storage = Storage('calendar.dat')
credentials = storage.get()
if credentials is None or credentials.invalid == True:
	credentials = run(FLOW, storage)

# Create an httplib2.Http object to handle our HTTP requests and authorize it
# with our good Credentials.
http = httplib2.Http()
http = credentials.authorize(http)

# Build a service object for interacting with the API. Visit
# the Google APIs Console
# to get a developerKey for your own application.
google_calendar = build(serviceName='calendar', version='v3', http=http,
	developerKey=config.get('google', 'developer_key'))
	
