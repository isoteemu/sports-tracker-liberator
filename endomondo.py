#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

""" Simple API for accessing Endomondo data.

Provides Endomondo API wrapper, which uses Endomondo mobile API
instead of HTML scrapping. Only some features are currently implemented,
but as Endomondo app uses HTTP, it's somewhat easy to implemented rest.
To retrieve network stream from from andoid, run on adb shell:
	tcpdump -n -s 0 -w -| nc -l -p 11233

and on Linux:
	adb forward tcp:11233 tcp:11233
	nc 127.0.0.1 11233 | wireshark -k -S -i -

To use, first authenticat client. Currently it seems that auth_token is
never changed, so only once is necessary and storing auth_toke somewhere
should be sufficient:

	sports_tracker = Endomond('user@email.com', 'password')
	for workout in sports_tracker.workout_list():
		print workout.summary

OR

	sports_tracker = Endomond()
	sports_tracker.auth_token = '***blahblah***'

"""

import requests
# For deviceId generation
import uuid, socket

from datetime import datetime, timedelta

class Endomondo:
	# Some parameters what Endomondo App sends.
	country = 'GB'
	device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()))
	os = "Android"
	app_version="7.1"
	app_variant="M-Pro"
	os_version="2.3.7"
	model="HTC Vision"

	# Auth token - seems to stay same, even when disconnecting - Security flaw in Endomondo side, but easy to fix on server side.
	auth_token = None

	# Using session - provides keep-alive in urllib3
	Requests = requests.session()

	# Authentication url. Special case.
	URL_AUTH		= 'https://api.mobile.endomondo.com/mobile/auth?v=2.4&action=PAIR'
	# Page for latest workouts.
	URL_WORKOUTS	= 'http://api.mobile.endomondo.com/mobile/api/workout/list?maxResults=40'
	# Running track
	URL_TRACK	= 'http://api.mobile.endomondo.com/mobile/readTrack'
	# Music track
	URL_PLAYLIST	= 'http://api.mobile.endomondo.com/mobile/api/workout/playlist'

	sports_map = {
		2: 'Cycling, sport',
		1: 'Cycling, transport',
		14: 'Fitness walking',
		15: 'Golfing',
		16: 'Hiking',
		21: 'Indoor cycling',
		9: 'Kayaking',
		10: 'Kite surfing',
		3: 'Mountain biking',
		17: 'Orienteering',
		19: 'Riding',
		5: 'Roller skiing',
		11: 'Rowing',
		0: 'Running',
		12: 'Sailing',
		4: 'Skating',
		6: 'Skiing, cross country',
		7: 'Skiing, downhill',
		8: 'Snowboarding',
		20: 'Swimming',
		18: 'Walking',
		13: 'Windsurfing',
		22: 'Other',
		23: 'Aerobics',
		24: 'Badminton',
		25: 'Baseball',
		26: 'Basketball',
		27: 'Boxing',
		28: 'Climbing stairs',
		29: 'Cricket',
		30: 'Elliptical training',
		31: 'Dancing',
		32: 'Fencing',
		33: 'Football, American',
		34: 'Football, rugby',
		35: 'Football, soccer',
		49: 'Gymnastics',
		36: 'Handball',
		37: 'Hockey',
		48: 'Martial arts',
		38: 'Pilates',
		39: 'Polo',
		40: 'Scuba diving',
		41: 'Squash',
		42: 'Table tennis',
		43: 'Tennis',
		44: 'Volleyball, beach',
		45: 'Volleyball, indoor',
		46: 'Weight training',
		47: 'Yoga',
		50: 'Step counter',
		87: 'Circuit Training',
		88: 'Treadmill running',
		89: 'Skateboarding',
		90: 'Surfing',
		91: 'Snowshoeing',
		92: 'Wheelchair',
		93: 'Climbing',
		94: 'Treadmill walking'
	}
	
	def __init__(self, email=None, password=None):
		
		self.Requests.headers['User-Agent'] = "Dalvik/1.4.0 (Linux; U; %s %s; %s Build/GRI40)" % (self.os, self.os_version, self.model)

		if email and password:
			self.auth_token = self.request_auth_token(email, password)

	def get_auth_token(self):
		if self.auth_token:
			return self.auth_token
		self.auth_token = self.request_auth_token()
		return self.auth_token

	def request_auth_token(self, email, password):
		params = {
			'email':			email,
			'password':		password,
			'country':		self.country,
			'deviceId':		self.device_id,
			'os'	:			self.os,
			'appVersion':	self.app_version,
			'appVariant':	self.app_variant,
			'osVersion':		self.os_version,
			'model':			self.model
		}

		r = self.Requests.get(self.URL_AUTH, params=params)

		lines = r.text.split("\n")
		if lines[0] != "OK":
			raise ValueError("Could not authenticate with Endomondo, Expected 'OK', got '%s'" % lines[0])

		lines.pop(0)
		for line in lines:
			key, value = line.split("=")
			if key == "authToken":
				return value
		
		return False

	# Helper for generating requests - can't be used in athentication.
	def make_request(self, url, params={}):
		params.update({
			'authToken':	self.get_auth_token(),
			'language':	'EN'
		})
		r = self.Requests.get(url, params=params)

		if r.status_code != requests.codes.ok:
			print "Could not retrieve URL %s" % r.url
			r.raise_for_status()

		return r

	# Retrieve latest workouts.
	def workout_list(self):
		r = self.make_request(self.URL_WORKOUTS)

		workouts = []
		for entry in r.json['data']:
			workout = EndomondoWorkout(self)
			
			workout.id = entry['id']

			if entry.has_key('name'):
				workout.summary = entry['name']
			elif self.sports_map.has_key(entry['sport']):
				workout.summary = self.sports_map[entry['sport']]
			else:
				print self.sports_map
				print "Sports entry: %s" % entry['sport']
				workout.summary = 'Sports'		

			workout.start_time = self._parse_date(entry['start_time'])
			workout.end_time   = workout.start_time + timedelta(seconds=entry['duration_sec'])

			if entry.has_key('note'):
				workout.note = entry['note']

			if entry['has_points'] == True:
				self._location = False

			workouts.append(workout)

		return workouts

	def _parse_date(self, date):
		return datetime.strptime(date, "%Y-%m-%d %H:%M:%S %Z")

		
""" Workout class. Bad design. """

class Workout:
	"""
	Data params. Endomondo provides a bunch of them, but we are only interested on some
	"""
	start_time = None
	end_time = None
	id = 0
	sport = 0
	summary = ""
	note = ""
	location = ""
	
	# Creator
	sports_tracker = None
	def __init__(self, sports_tracker):
		self.sports_tracker = sports_tracker

class EndomondoWorkout(Workout):
	_location = None

	def location(self):
		if self._location == False:
			self._location = None
			r = self.sports_tracker.make_request(self.sports_tracker.URL_TRACK, {'trackId': self.id})
			lines = r.text.split("\n");
			if len(lines) < 2:
				return self._location

			data = lines[2].split(";")
			if data[2] == "" or data[3] == "":
				return self._location

			geocode_params = {
				'latlng': data[2]+","+data[3],
				'sensor': 'false'
			}
			g_r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=geocode_params)
			if g_r.status_code == requests.codes.ok and g_r.json['status'] == 'OK':
				self._location = g_r.json['results'][0]['formatted_address']
		return self._location

