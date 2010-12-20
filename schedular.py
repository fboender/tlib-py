# Copyright (c) 2010 Ferry Boender
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

__VERSION__ = (0, 1)

"""
Cron-like scheduling module.
"""

import datetime

class Scheduler(object):
	"""
	Cron-like scheduling class. Usage:

	>>> def cb_func(p1, p2):
	...   print p1, p2
	...
	>>> s = Scheduler()
	# Run every 20 seconds on Saturday and Sunday during Januari
	>>> s.add_task(cb_func, ('hello', 'world'), [0, 20, 40], '*', '*', 1, [5, 6])
	# Run once every hour
	>>> s.add_task(cb_func, ('goodbye', 'world'), 0, '*', '*', '*', '*')
	"""
	def __init__(self):
		self.tasks = []
		self.lastseen = {'hour': None, 'minute': None}

	def add_task(self, cb_func, cb_params, minute = '', hour = '', dom = '', month = '', dow = ''):
		"""
		Add a task to the scheduler. cb_func is the callable to
		call when the task is executed. cb_params is a set or
		list of parameters to pass to the callback function.
		minute, hour, dom (day of month), month and dow (Day of
		Week; 0 = monday, 6 = sunday) can be a set or list of
		times to run at, a string with a comma-seperated values
		to run at or '*' for every minute, hour, etc.

		Examples:

		Run every Saturday and Sunday at 12:00:
		>>> s.add_task('0', '12', '*', '*', [5, 6])

		Run every 20 minutes:
		>>> s.add_task('0, 20, 40', '*', '*', '*', '*')
		"""
		self.tasks.append((
			cb_func,
			cb_params,
			self._t_to_sint(minute),
			self._t_to_sint(hour),
			self._t_to_sint(dom),
			self._t_to_sint(month),
			self._t_to_sint(dow),
		))

	def run_once(self):
		"""
		Perform one check of the tasks to see if any of them
		should be run. If so, the task is executed by calling the
		supplied callback function with the given parameters.

		This function should be called once every minute, at the
		least.
		"""
		now = datetime.datetime.now()
		if self.lastseen['hour'] == now.hour and \
			self.lastseen['minute'] == now.minute:
			return

		self.lastseen['hour'] = now.hour
		self.lastseen['minute'] = now.minute
		for task in self.runlist(now):
			task[0](*task[1])

	def runlist(self, dt):
		"""
		Generate a list of tasks to run at datetime `dt`.
		"""
		runtasks = []

		for t in self.tasks:
			if ('*' in t[2] or dt.minute in t[2]) and \
				('*' in t[3] or dt.hour in t[3]) and \
				('*' in t[4] or dt.day in t[4]) and \
				('*' in t[5] or dt.month in t[5]) and \
				('*' in t[6] or dt.weekday() in t[6]):
				runtasks.append(t)
		return runtasks

	def _t_to_sint(self, x):
		"""
		Convert a time-slice parameter (self.add_task) and split
		it up/convert it to integers.
		"""

		if type(x) == type(int()):
			return [x, ]
		if type(x) == type(''):
			if '*' in x: 
				return ['*', ]
			else:
				return [int(i) for i in x.split(',')]
		elif type(x) == type([]):
			if '*' in x: 
				return ['*', ]
			else:
				return [int(i) for i in x]
		else:
			raise ValueError('Invalid type or value \'%s\'' % (x))

if __name__ == "__main__":
	import time

	def f(*args):
		print args

	s = Scheduler()
	s.add_task(f, (1, ), '*', '*', '*', '*', '*')
	s.add_task(f, (2, ), '*', '*', '*', '*', [4, 6])
	s.add_task(f, (3, ), '0, 14', 5, 2, 8, [0, 5, 6])
	s.add_task(f, (4, ), '0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20', '*', '*', '*', '*')
	s.add_task(f, (5, ), '5, 10, 13, 20, 30', '*', '*', '*', '*')
	s.add_task(f, (6, ), [20, 30], '*', '*', '*', '*')
	while True:
		tasks = s.run_once()
		if tasks:
			print datetime.datetime.now()
			for t in tasks:
				print "Running task:", t
			print
		time.sleep(1)

