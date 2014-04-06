# -*- coding: utf-8 -*-

from datetime import datetime, tzinfo
import gzip, StringIO

def str_to_datetime(date):
	''' Convert string presentation into datetime object.
	'''
	return datetime.strptime(date, "%Y-%m-%d %H:%M:%S %Z")

def datetime_to_str(date):
	''' Convert datetime object into string presentation
		TODO: Convert local timezone to UTC.
	'''
	if type(date) == str:
		return date

	if date.tzinfo != None:
		date = date.astimezone(tzinfo('UTC'))
	text = date.strftime('%Y-%m-%d %H:%M:%S UTC')
	return text

def chunks(l, n):
	""" Yield successive n-sized chunks from l.
		From https://stackoverflow.com/a/312464
	"""
	for i in xrange(0, len(l), n):
		yield l[i:i+n]

def gzip_string(data):
	''' Android/Java compatible gziping.
		Sucks ass - pythons zlib that is. In PHP one can do same by gzdeflate()
	'''

	stringio = StringIO.StringIO()
	gfp = gzip.GzipFile(fileobj=stringio, mode='w')
	gfp.write(data)
	gfp.close()

	return stringio.getvalue()
