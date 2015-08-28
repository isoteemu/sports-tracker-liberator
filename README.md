# Sports Tracker Liberator

Under a catchy name lies an implementation which uses/implements Endomondo Mobile Api.

## Status

Currently only Endomondo Api is somewhat implemented. Retrieving stuff somewhat works, and submitting new workouts works as in most basic form. All social media crap is ignored.

## Usage

### Authentication

Endomondo implements basic token mechanism, except that earlier versions didn't do that correctly and was only protected by *can't be arsed with it* -securitysystem. Later App versions tried to fix this, while maintaining backward compatibility by implementing a second, `secureToken` param. This is mainly used for social media crap, so we'll conveniently ignore it.

To authenticate, one needs existing email and password:

	from endomondo import MobileApi
	endomondo = MobileApi(email='email@example.com', password='p4ssw0rd')

	auth_token = endomondo.get_auth_token()

This will return an `auth_token`, which can be stored on keychain or similar. In future, it should be used to skip whole login juggalloo.

	endomondo = MobileApi(auth_token=auth_token)

### Retrieving workouts:
To retrieve latest workouts:

	endomondo.get_workouts()

Endomondo Mobile Api provides some oddities, and one of them is that `maxResults` actually work! And as usually in REST APIs, `before` date can be defined:

	workouts = endomondo.get_workouts(maxResults=2)
	endomondo.get_workouts(before=workouts[-1].start_time)

Structure for `workouts` page is similar to other providers, except paging links are missing.

### Retrieving single workout

`MobileApi.get_workout()` accepts either existing workout, or workout ID.

	workout = endomondo.get_workout(workoutId='234246')
	[...]
	reload = endomondo.get_workout(workout)

For workouts, or workout history, you can pass `fields` param to define, which attributes you are interested at. Again, a bit suprisingly, this works.

	social_workout = endomondo.get_workout(fields=['lcp_count'])

Thease attributes aren't documented anywhere, but most of known can be found ín `MobileApi.get_workout()`, and they follow somewhat logical naming conventions.

### Creating a workout and a track.

Some, if not most of program logic lies in mobile app, and server just stores data. This means that one needs to calculate most of their data by themselves.

Currently only most basic workout creation is supported. Later if/when workout update is added, more features becomes available. This is somewhat related to implementation of Endomondo Mobile Api, as only sport type, calories, hydration, duration and distance in form of track point is created. After initial creation, rest of data is updated to it.

To create workout:

	from endomondo import MobileApi, Workout, TrackPoint
	from datetime import datetime

	endomondo = MobileApi(auth_token='1234')

	workout = Workout()

	workout.start_time = datetime.utcnow()

	# See ``workout.sports``
	workout.sport = 0

	# Units are in user' local units, and only Metric is supported.
	# `distance` is in km.
	# Note that at creation time, this is not required. It's only used for automatic track point generation.
	workout.distance = 1.5

	# Duration in seconds
	workout.duration = 600

	endomondo.post_workout(workout=workout, properties={'audioMessage': 'false'})

	if workout.id:
		print "Saved!"

Altought track points aren't technically required by Endomondo backend, which is likely just for a sake of backwards compatibility, and in practice you always want to have at least one `TrackPoint` in your `Workout`. `MobileApi.post_workout()` can automate this, and will create one if none exists.

### Other

For other, tested, functionality see `main.py`

## Disclaimer, legalese and everything else.

This is _not_ affiliated or endorset by Endomondo, or any other party. If you are copying this for a commercial project, be aware that it *might* be so that clean room implementation rules aren't fully complied with.
