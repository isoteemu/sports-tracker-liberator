# -*- coding: utf-8 -*-

from .utils import str_to_datetime

from datetime import datetime
import logging

PRIVACY_PUBLIC	= 0
PRIVACY_FRIENDS	= 1
PRIVACY_PRIVATE	= 2

sports = {
	0:	'Running',
	1:	'Cycling, transport',
	2:	'Cycling, sport',
	3:	'Mountain biking',
	4:	'Skating',
	5:	'Roller skiing',
	6:	'Skiing, cross country',
	7:	'Skiing, downhill',
	8:	'Snowboarding',
	9:	'Kayaking',
	10:	'Kite surfing',
	11:	'Rowing',
	12:	'Sailing',
	13:	'Windsurfing',
	14:	'Fitness walking',
	15:	'Golfing',
	16:	'Hiking',
	17:	'Orienteering',
	18:	'Walking',
	19:	'Riding',
	20:	'Swimming',
	21:	'Indoor cycling',
	22:	'Other',
	23:	'Aerobics',
	24:	'Badminton',
	25:	'Baseball',
	26:	'Basketball',
	27:	'Boxing',
	28:	'Climbing stairs',
	29:	'Cricket',
	30:	'Elliptical training',
	31:	'Dancing',
	32:	'Fencing',
	33:	'Football, American',
	34:	'Football, rugby',
	35:	'Football, soccer',
	36:	'Handball',
	37:	'Hockey',
	38:	'Pilates',
	39:	'Polo',
	40:	'Scuba diving',
	41:	'Squash',
	42:	'Table tennis',
	43:	'Tennis',
	44:	'Volleyball, beach',
	45:	'Volleyball, indoor',
	46:	'Weight training',
	47:	'Yoga',
	48:	'Martial arts',
	49:	'Gymnastics',
	50:	'Step counter',
	87:	'Circuit Training',
	88:	'Treadmill running',
	89:	'Skateboarding',
	90:	'Surfing',
	91:	'Snowshoeing',
	92:	'Wheelchair',
	93:	'Climbing',
	94:	'Treadmill walking'
}

class Workout(object):

	''' Workout object.
		:param id: Workout key.
		:param name: Optional User provided name.
		:param heart_rate_avg: Average heart rate.
		:param heart_rate_max: Maximum heart rate.
		:param owner_id: Workout creator ID.
		:param privacy_workout: Workout privacy. See: ``PRIVACY_PUBLIC``, ``PRIVACY_FRIENDS``, and ``PRIVACY_PRIVATE``
		:param privacy_map: Workout track privacy. See: ``PRIVACY_PUBLIC``, ``PRIVACY_FRIENDS``, and ``PRIVACY_PRIVATE``
		:param distance: Traveled distance.
		:param lcp_count: Social media count crap.
		:param calories: Estimate of burned calories.
		:param weather: Weather types follow accuweather types.
		:param feed: Endomondos' own social media crap.
		:param speed_avg: Average speed.
		:param speed_max: Maximum achieved speed.
		:param sport: Sport type. See: ``sports``
		:param device: Devide understanding of workout. When new workout is created, app creates own ID for it for what it then tries to request
	'''

	id 				= None

	name			= ''

	heart_rate_avg	= None
	heart_rate_max	= None

	owner_id		= 0

	privacy_workout	= PRIVACY_PRIVATE
	privacy_map		= PRIVACY_PRIVATE

	distance 		= 0.0
	calories		= None

	message			= ''
	lcp_count		= {
		'peptalks':	0,
		'likes':	0,
		'comments':	0
	}

	weather			= {
		'weather_type': 0
	}

	feed			= {
		'story': ''
	}

	speed_avg		= 0.0
	speed_max		= 0

	sport			= 0

	descent			= 0.0
	ascent			= 0.0
	altitude_min	= 0.0
	altitude_max	= 0.0

	hydration		= None
	burgers_burned	= 0

	steps			= 0
	cadence_max		= 0

	device			= {
		'workout_id':	0
	}

	_points = []

	_start_time		= None
	_duration		= None

	_live			= False
	''' Stuff not implemented
	polyline_encoded_small = ""
	'''

	def __init__(self, properties={}):

		#super(Workout, self).__init__()

		properties.setdefault('start_time', datetime.utcnow())

		if properties.has_key('sport'):
			properties.setdefault('name', sports.get(properties['sport']))

		for key in properties:
			#if key != "points":
			logging.debug("setting property: %s = %s" % (key,properties[key]))
			setattr(self, key, properties[key])

	def addPoint(self, point):
		self._points.append(point)

	@property
	def duration(self):
		''' Return excercise duration. Calculate from points, if missing.
		'''
		if self._duration:
			return self._duration

		self._duration = 0

		youngest = None

		for point in self.points:
			if youngest:
				youngest = max(point.time, youngest)
			else:
				youngest = point.time

		start_time = self.start_time
		if youngest and start_time < youngest:
			time_diff = youngest - start_time
			self.duration = time_diff.total_seconds()

		return self._duration

	@duration.setter
	def duration(self, value):
		self._duration = int(value)

	@property
	def start_time(self):
		if not self._start_time:
			oldest = datetime.utcnow()
			for point in self.points:
				oldest = min(point.time, oldest)
			self.start_time = oldest

		return self._start_time

	@start_time.setter
	def start_time(self, value):
		if isinstance(value, datetime):
			self._start_time = value
		else:
			self._start_time = str_to_datetime(value)

		return self._start_time

	@property
	def points(self):
		return self._points

	@points.setter
	def points(self, points):
		for point in points:
			self.addPoint(TrackPoint(point))

	@property
	def live(self):
		return self._live

	@live.setter
	def live(self, value):
		self._live = bool(value)
		return self._live
	

class TrackPoint(object):

	''' Track measurement point.
		:param hr:	Heart rate.
		:param time: Measurement time
		:param speed: Current speed
		:param alt: Altitude
		:param lng: Longitude
		:param lat: Latitude
		:param dist: Distance from start
		:param inst: Don't know.
	'''

	hr		= ''
	_time	= ''
	speed	= ''
	alt		= ''
	lng		= ''
	lat		= ''
	dist	= ''
	inst	= ''

	def __init__(self, properties):
		properties.setdefault('time', datetime.utcnow())
		for key in properties:
			setattr(self, key, properties[key])

	@property
	def time(self):
		return self._time

	@time.setter
	def time(self, value):
		if isinstance(value, datetime):
			self._time = value
		else:
			self._time = str_to_datetime(value)

		return self._time


