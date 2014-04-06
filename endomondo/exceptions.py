# -*- coding: utf-8 -*-
'''
Exceptions
'''

class EndomondoException(RuntimeError):
	''' Base class for Endomondo API related errors '''

class NotFoundException(EndomondoException):
	''' Requested item was not found in Endomondo database '''

class AuthenticationError(ValueError):
	''' Could not authenticate into Endomondo '''
