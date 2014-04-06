# -*- coding: utf-8 -*-

from . import __version__, __title__
from .workout import sports, Workout, TrackPoint
from .utils import chunks, str_to_datetime, datetime_to_str, gzip_string
from .exceptions import *

import platform
import uuid, socket
import random
from datetime import datetime, timedelta

import requests
import zlib
import json

import logging

URL_AUTHENTICATE	= 'https://api.mobile.endomondo.com/mobile/auth'
URL_WORKOUTS		= 'https://api.mobile.endomondo.com/mobile/api/workouts'
URL_WORKOUT_GET 	= 'https://api.mobile.endomondo.com/mobile/api/workout/get'
URL_WORKOUT_POST	= 'https://api.mobile.endomondo.com/mobile/api/workout/post'
URL_TRACK			= 'https://api.mobile.endomondo.com/mobile/track'
URL_PLAYLIST		= 'https://api.mobile.endomondo.com/mobile/playlist'

URL_ACCOUNT_GET		= 'https://api.mobile.endomondo.com/mobile/api/profile/account/get'
URL_ACCOUNT_POST	= 'https://api.mobile.endomondo.com/mobile/api/profile/account/post'

UNITS_METRIC		= 'METRIC'
UNITS_IMPERIAL		= 'IMPERIAL'

GENDER_MALE			= 'MALE'
GENDER_FEMALE		= 'FEMALE'

'''
	Playlist items are sent one-by-one, using post and in format:
	>>> 1;I Will Survive;Gloria Gaynor;;;;2014-04-05 17:22:56 UTC;2014-04-05 17:23:26 UTC;;
	[...]
	>>> 6;Holding Out for a Hero;Bonnie Tyler;;;;2014-04-05 17:38:46 UTC;2014-04-05 17:44:47 UTC;<lat>;<lng>
'''

class MobileApi(object):

	auth_token		= None
	secure_token	= None

	Requests		= requests.session()

	''' Details which Endomondo app sends back to home.
		If, for some reason, endomondo blocks this library, thease are likely what values they are using to validate against.
	'''
	device_info		= {
		'os':			platform.system(),
		'model':		platform.python_implementation(),
		'osVersion':	platform.release(),
		'vendor':		'github/isoteemu',
		'appVariant':	__title__,
		'country':		'GB',
		'v':			'2.4', # No idea, maybe api version?
		'appVersion':	__version__,
		'deviceId':		str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname())),
	}

	def __init__(self, **kwargs):
		'''
			:param auth_token: Optional Previous authentication token to use.
			:param email: Optional Authentication email.
			:param password: Optional Authentication password.
		'''
		email = kwargs.get('email')
		password = kwargs.get('password')

		if kwargs.get('auth_token'):
			self.set_auth_token(kwargs.get('auth_token'))
		elif email and password:
			self.set_auth_token(self.request_auth_token(email, password))

		if self.device_info['os'] in ['Linux']:
			self.device_info['vendor'] = platform.linux_distribution()[0]

		'''	User agent in endomondo app v. 10.1.1 is as:
			com.endomondo.android.pro/10.1.1 (Linux; U; Android {android_version}; {locality}; {build_model}; {phone_build_specific}) {resolution} {manufacturer} {model}
		'''
		self.Requests.headers['User-Agent'] = '{appVariant}/{appVersion} ({os}; {osVersion}; {model}) {vendor}'.format(**self.device_info)

	def get_auth_token(self):
		return self.auth_token

	def set_auth_token(self, auth_token):
		self.auth_token = auth_token

	def request_auth_token(self, email, password):
		''' Retrieve authentication token.
			:param email: Endomondo login email
			:param password: Endomondo login password

			At version 10.1.1, returned values are:
			action=PAIRED
			authToken=<authtoken>
			measure=METRIC
			displayName=<name>
			userId=<uid>
			facebookConnected=<true|false>
			secureToken=<securetoken>

			secureToken is quite new, and needed for personal data retrieval.
		'''

		params = self.device_info
		params.update({
			'action':	'pair',
			'email':	email,
			'password':	password
		})

		r = self.Requests.get(URL_AUTHENTICATE, params=params)

		lines = r.text.split("\n")
		if lines[0] != "OK":

			logging.warning("Logging failed into Endomondo, returned data was: %s" % r.text)
			raise AuthenticationError("Could not authenticate with Endomondo, Expected 'OK', got '%s'" % lines[0])

		lines.pop(0)
		for line in lines:
			key, value = line.split("=")
			if key == "authToken":
				return value

		return False

	def make_request(self, url, params={}, method='GET', data=None, **kwargs):
		''' Helper for generating requests - can't be used in athentication.

		:param url: base url for request.
		:param params: additional parameters to be passed in GET string.
		'''

		params.setdefault('authToken', self.auth_token)
		params.setdefault('language', 'en')

		# Flatten 'fields'
		if type(params.get('fields')) is list:
			params['fields'] = ','.join(params['fields'])

		if data and params.get('gzip') == 'true':
			data = gzip_string(data)
		elif data and params.get('deflate') == 'true':
			data = zlib.compress(data)

		r = self.Requests.request(method, url, data=data, params=params, **kwargs)

		if r.status_code != requests.codes.ok:
			logging.debug('Endomondo returned failed status code. Code: %s, message: %s' % (r.status_code, r.text))

		r.raise_for_status()

		'''
		# Endomondo has an odd way of randomly compressing things
		# TODO: Implement gzip
		if params.get('compression') == 'deflate':
			try:
				text = zlib.decompress(r.content)
				r._content = text
			except zlib.error as e:
				logging.warning('Could not decompress endomondo returned data, even thought deflate was requested. Error: %s' % e)
		'''
		try:
			data = r.json()
			if data.has_key('error'):
				logging.warning('Error loading data from Endomondo. Type: %s', data['error'].get('type'))

				err_type = data['error'].get('type')
				if err_type == 'AUTH_FAILED':
					raise AuthenticationError('Authentication token was not valid.')

		except:
			'''pass'''

		return r

	def get_account_info(self, **kwargs):
		''' Return data about current account.
			:param fields: Properties to retrieve. Default is `hr_zones`,`emails`.
			:return: Json object. Default fields:
			>>> {"data":{
			>>> 	"hr_zones":{"max":202,"z1":131,"z4":174,"z5":188,"z2":145,"z3":159,"rest":60},
			>>>		"weight_kg":int(),
			>>>		"phone":str("+3585551234"),
			>>>		"sex":str(<GENDER_MALE|GENDER_FEMALE>),
			>>>		"sync_time":datetime(),
			>>>		"date_of_birth":datetime(),
			>>>		"emails":[{"id":int(),"email":str('email@example.com'),"verified":bool(),"primary":bool()}],
			>>>		"lounge_member":bool(),
			>>>		"favorite_sport":int(),
			>>>		"units":str(<UNITS_METRIC|UNITS_IMPERIAL>,
			>>>		"country":str("CC"),
			>>>		"id":int(),
			>>>		"time_zone":str("+02:00"),
			>>>		"first_name":str("name"),
			>>>		"middle_name":str("middle"),
			>>>		"last_name":str("lastname"),
			>>>		"favorite_sport2":int(),
			>>>		"weight_time":datetime(),
			>>>		"created_time":datetime(),
			>>>		"height_cm":int()
			>>> }}
		'''

		kwargs.setdefault('fields', ['hr_zones','emails'])

		# App uses compressions for both ways, we don't handle that yet.
		#kwargs.setdefault('compression', 'deflate')
		kwargs.setdefault('deflate', 'true')

		r = self.make_request(URL_ACCOUNT_GET, params=kwargs)

		data = r.json()

		# Convert into datetime objects
		date_of_birth 	= data['data'].get('date_of_birth')
		sync_time		= data['data'].get('sync_time')
		weight_time		= data['data'].get('weight_time')

		if date_of_birth:
			data['data']['date_of_birth'] = str_to_datetime(date_of_birth)
		if sync_time:
			data['data']['sync_time'] = str_to_datetime(sync_time)
		if weight_time:
			data['data']['weight_time'] = str_to_datetime(weight_time)

		return data

	def post_account_info(self, account_info={}, **kwargs):
		''' Save user info.

			:param account_info: Dict of propeties to post. Known are:
			>>> {
			>>> 	"weight_kg":int(),
			>>> 	"first_name":str("name"),
			>>>		"sex":<GENDER_MALE|GENDER_FEMALE>,
			>>>		"middle_name":str("Middlename"),
			>>>		"last_name":str("Familyname"),
			>>>		"date_of_birth":datetime(),
			>>>		"height_cm":int(),
			>>>		"units":<UNITS_IMPERIAL|UNITS_METRIC>
			>>>	}
		'''

		# Endomondo App uses deflate, but at current time it's not implemented.
		#kwargs.setdefault('compression', 'deflate')
		kwargs.setdefault('deflate', 'true')


		if account_info.has_key('date_of_birth'):
			account_info['date_of_birth'] = datetime_to_str(account_info.get('date_of_birth'))

		data = json.dumps(account_info)

		r = self.make_request(URL_ACCOUNT_POST, params=kwargs, method='POST', data=data)
		return r.json()

	def get_workouts(self, before=None, **kwargs):
		''' Return list of workouts
			:param before: Optional datetime object or iso format date string (%Y-%m-%d %H:%M:%S UTC)
			:param maxResults: Optional Maximum number of workouts to be returned. Default is 20
			:param deflate: Optional true or false. Default is false, whereas endomondo app default is true. Untested.
			:param fields: Optional Comma separated list for endomondo properties to return. Default is: device,simple,basic,lcp_count
		'''

		kwargs.setdefault('maxResults', 20)
		# Default fields used by Endomondo 10.1 App
		kwargs.setdefault('fields', ['device', 'simple', 'basic', 'lcp_count'])

		# Flatten 'before'
		if before != None:
			if isinstance(before, datetime):
				kwargs['before'] = datetime_to_str(before)
			elif type(before) is str:
				kwargs['before'] = before
			else:
				raise ValueError("Param 'before' needs to be datetime object or iso formatted string.")

		if kwargs.get('deflate') == 'true':
			kwargs.setdefault('compression', 'deflate')

		r = self.make_request(URL_WORKOUTS, kwargs)

		workouts = []

		for entry in r.json().get('data', []):
			workout = self.build_workout(entry)
			workouts.append(workout)
			#print '[{id}] {start_time}: {name}'.format(entry)

		return workouts

	def get_workout(self, workout, **kwargs):
		''' Retrieve workout.
			:param workout: Workout ID, or ``Workout`` object to retrieve
			:param fields: Optional list of endomondo properties to request
		'''

		# Default fields used by Endomondo 10.1 App
		kwargs.setdefault('fields', [
			'device', 'simple','basic', 'motivation', 'interval',
			'hr_zones', 'weather', 'polyline_encoded_small', 'points',
			'lcp_count', 'tagged_users', 'pictures', 'feed'
		])

		if isinstance(workout, Workout):
			kwargs.setdefault('workoutId', workout.id)
		else:
			kwargs.setdefault('workoutId', int(workout))

		r = self.make_request(URL_WORKOUT_GET, kwargs)
		data = r.json()

		if data.has_key('error'):
			err_type = data['error'].get('type')
			if err_type == 'NOT_FOUND':
				raise NotFoundException('Item ``%s`` was not found in Endomondo.' % kwargs['workoutId'])
			else:
				raise EndomondoException('Error while loading data from Endomondo: %s' % err_type)

		workout = self.build_workout(data)
		return workout

	def build_workout(self, properties):
		''' Helper to build ``Workout`` model from request response.'''
		workout = Workout(properties)
		return workout

	def post_workout(self, workout, properties={}):
		''' Post workout in endomondo.

			At most basic, it should look like: 
            [workoutId] => -8848933288523797092
            [sport] => 46
            [duration] => 180
            [gzip] => true
            [audioMessage] => true
            [goalType] => BASIC
            [extendedResponse] => true
            [calories] => 18
            [hydration] => 0.012676

			:param workout: Workout object
			:param properties: Additional properties.
		'''

		properties.setdefault('audioMessage', 'true')
		properties.setdefault('goalType', 'BASIC')
		properties.setdefault('extendedResponse', 'true')

		# A "Bug" in endomondo infrastructure; If gzip is not defined, Endomondo
		# will complain about missing TrackPoints (not directly related to ``Workout.TrackPoint``)
		properties.setdefault('gzip', 'true')

		if not workout.device['workout_id']:
			workout.device['workout_id'] = random.randint(-9999999999999999999, 9999999999999999999)

		if workout.id:
			properties.setdefault('workoutId', workout.id)
		else:
			properties.setdefault('workoutId', workout.device['workout_id'])
		
		properties.setdefault('sport', workout.sport)
		properties.setdefault('calories', workout.calories)
		properties.setdefault('duration', workout.duration)
		properties.setdefault('hydration', workout.hydration)
		properties.setdefault('heartRateAvg', workout.heart_rate_avg)

		# Create pseudo point, if none exists
		if len(workout.points) == 0:
			point = TrackPoint({
				'time':	workout.start_time,
				'dist':	workout.distance,
				'inst': '3'
			})
			workout.addPoint(point)

		# App posts only 100 items, so multiple submissions might be needed.
		for chunk in chunks(workout.points,100):
			
			data = '\n'.join([self.flatten_trackpoint(i) for i in chunk])
			data = data+"\n"

			r = self.make_request(URL_TRACK, params=properties, method='POST', data=data)

			lines = r.text.split("\n")
			if lines[0] != 'OK':
				raise EndomondoException('Could not post track. Error ``%s``. Data may be partially uploaded' % lines[0])

			workout.id = int(lines[1].split('=')[1])

		logging.debug("Saved workout ID: %s" % workout.id)

		return workout

	def flatten_trackpoint(self, track_point):
		''' Convert ``TrackPoint`` into Endomondo textual presentation
			:param track_point: ``TrackPoint``.
		'''

		data = {
			'time':		datetime_to_str(track_point.time),
			'lng':		track_point.lng,
			'lat':		track_point.lat,
			'dist':		round(track_point.dist,2),
			'speed':	track_point.speed,
			'alt':		track_point.alt,
			'hr':		track_point.hr,
			'inst':		track_point.inst
		}

		text = u'{time};{inst};{lat};{lng};{dist};{speed};{alt};{hr};'.format(**data)
		return text
