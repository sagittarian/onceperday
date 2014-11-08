#!/usr/bin/python3
'''Run a task once per day, at a (pseudo-)random time.

You can pass in a function, and this module will run it if it is later
than a certain point in the day (determined per day).  It will then
cache the fact of having run the command (as well as any output from
the function), so that subsequent runs during the same day will not run it again.

'''

#import configparser
import datetime
import os

import rand

class OncePerDay:
	configdir = os.path.expanduser('~/.config/onceperday')

	def __init__(self, func, slug, execute=True):
		'''func is the function that will be called once per day;
		its output will be saved in a cache file.
		slug identifies this task for the purpose of caching.
		'''
		os.makedirs(self.configdir, exist_ok=True)

		self.func = func
		self.slug = slug
		self.cachefile = os.path.join(self.configdir, slug)

		if execute:
			self.execute()

	@staticmethod
	def sec2time(s):
		h, s = divmod(s, 60 * 60)
		m, s = divmod(s, 60)
		return datetime.time(h, m, s)

	def secforday(self, ordinal=None):
		if ordinal is None:
			ordinal = datetime.date.today().toordinal()
		# we need to advance the PRNG at least 2 times, or successive
		# ordinals will still result in the same time of day.  We're
		# using 10 here to be sure.
		rnd = rand.Random(seed=ordinal).ranx(10)
		sec = int(rnd * 24*60*60)
		time = self.sec2time(sec)
		return time

	def checkcache(self, date, magic_point):
		'''Check if the function has already been run for the given date.'''
		if not os.path.exists(self.cachefile):
			return False
		datestr = date.isoformat()
		with open(self.cachefile) as f:
			for line in f:
				day, time, comment = line.split(maxsplit=2)
				if day == datestr:
					if time != magic_point.isoformat():
						raise ValueError('Bad time in cache line: {}'.format(line))
					return True
		return False

	def execute(self):
		'''Check if the magic point has already passed today, and the function
		has not yet been run'''
		magic_point = self.secforday()
		if magic_point > datetime.datetime.now().time():
			return	 # have yet to reach the point
		# now check the cache to see if we've already run the function
		today = datetime.date.today()
		if self.checkcache(today, magic_point):
			return
		result = str(self.func()) or ''
		if not result or result[-1] != '\n':
			result += '\n'
		with open(self.cachefile, 'a') as f:
			f.write('{} {}\t{}'.format(
				today.isoformat(), magic_point.isoformat(), result))
