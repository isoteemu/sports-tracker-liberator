#!/usr/bin/env python
# -*- coding: utf-8 -*-

from endomondo import Endomondo
from google import google_calendar
import ConfigParser

email = False
password = False
auth_token = False
calendar_id = None

# Google uses rfc3339 for dates.
def rfc3339(datetime):
	return datetime.strftime('%Y-%m-%dT%H:%M:%SZ%z')

config = ConfigParser.ConfigParser()
config.read(['config.ini.dist', 'config.ini'])

if not email:
	email = config.get('endomondo', 'email')
if not password:
	password = config.get('endomondo', 'password')
if not auth_token:
	auth_token = config.get('endomondo', 'auth_token')

if not calendar_id:
	calendar_id = config.get('google', 'calendar_id')

# FIXME If auth token is revoked, this isn't going to work.
if auth_token:
	endomondo = Endomondo()
	endomondo.auth_token = auth_token
else:
	if not email or not password:
		import kwallet
		wallet = kwallet.open_wallet()
		email, password = kwallet.get_auth(wallet)

	endomondo = Endomondo(email, password)
	if endomondo.auth_token:
		config.set('endomondo', 'auth_token', endomondo.auth_token)
		with open('config.ini', 'wb') as cfg_file:
			config.write(cfg_file)

workouts = endomondo.workout_list()

for workout in workouts:
	event = {
		'summary': workout.summary,
		'start': {
			'dateTime': rfc3339(workout.start_time)
		},
		'end': {
			'dateTime': rfc3339(workout.end_time)
		},
		'description': workout.note
	}

	if workout.location:
		event['location'] = workout.location()

	calendar_event = google_calendar.events().list(
		calendarId=calendar_id,
		timeMin=event['start']['dateTime'],
		timeMax=event['end']['dateTime'],
		q=event['summary']
		).execute()
		
	if calendar_event.has_key('items') and len(calendar_event['items']) >= 1:
		# TODO Check if self exists
		True
	else:
		print 'Creating event "%s"' % event['summary']
		google_calendar.events().insert(calendarId=calendar_id, body=event).execute()
