#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Commandline example for using Endomondo api
'''

import keyring

import sys
import getopt
import getpass

from datetime import datetime, timedelta

from endomondo import MobileApi, Workout, sports

from pprint import pprint

import logging, sys

if __name__ == '__main__':

	logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

	try:
		opts, args = getopt.getopt(sys.argv[1:], '', ['email=', 'pw='])
	except getopt.error, msg:
		print 'python %s --email=[email] --pw=[password]' % sys.argv[0]
		sys.exit(2)

	email = ''
	pw = ''

	auth_token = ''

	endomondoapi = MobileApi()

	for option, arg in opts:
		if option == '--email':
			email = arg
		elif option == '--pw':
			pw = arg

	while not email:
		email = raw_input('Please enter your endomondo email: ')

	auth_token = None
	if not pw:
		auth_token = keyring.get_password("endomondo", email)

	pprint(endomondoapi.device_info)

	while not auth_token:
		while not pw:
			print "No authentication token, using password authentication."
			pw = getpass.getpass()
			if not pw:
				print "Password can't be empty"

		try:
			auth_token = endomondoapi.request_auth_token(email=email, password=pw)
		except:
			pass

		if not auth_token:
			print "Did not receive valid authentication token."
			pw = ''
		else:
			keyring.set_password("endomondo", email, auth_token)

	endomondoapi.set_auth_token(auth_token)

	##
	## * Retrieve user profile info
	##
	user_data = endomondoapi.get_account_info()['data']
	print "Hello {first_name} {last_name}".format(**user_data)

	##
	## * Retrieve last workouts.
	##
	print "Your last 5 workouts:"
	for workout in endomondoapi.get_workouts( maxResults=5 ):
		print "[%s] %s at %s" % (workout.id, workout.name, workout.start_time)

	##
	## * Create new workout.
	##

	workout = Workout()

	workout_type = False
	while workout_type == False:
		# Ask for a workout type
		workout_type = raw_input('Workout type (p to print) [0]:')
		if workout_type == '':
			workout_type = '0'

		if workout_type == 'p':	
			for i in sports:
				print "%s:\t%s" % (i, sports[i])
			workout_type = False
		elif not workout_type.isdigit() or not sports.has_key(int(workout_type)):
			print "Key not found"
			workout_type = False
		else:
			workout.sport = int(workout_type)


	workout.name = raw_input('Workout name [%s]: ' % sports[workout.sport])
	while not workout.duration:
		duration = raw_input('Workout duration in seconds [300]: ')
		if duration is '':
			print "Using 5 minutes as duration"
			duration = 300
	
		elif not duration.isdigit():
			print "Please insert digit for duration"
			continue
	
		workout.duration = int(duration)
		workout.start_time = datetime.utcnow() - timedelta(seconds=workout.duration)

		workout.distance = workout.duration*0.0027777778
		# Calories is calculated on server side too.
		#workout.calories = int(workout.duration*0.26666667)

	#workout = endomondoapi.get_workout(w_id)

