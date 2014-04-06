# -*- coding: utf-8 -*-

'''
Unofficial Endomondo API library

:license: LGPL 2.1,  see LICENSE for more details.
'''

__title__ 	= 'sports-tracker-liberator'
__version__	= '0.2'
__build__	= 0x000200
__license__	= 'LGPL 2.1'

from . import utils
from .workout import sports, Workout, TrackPoint

from .endomondo import MobileApi

class Endomondo(MobileApi):
	''' Backwards compatibility '''
