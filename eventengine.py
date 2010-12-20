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

import sys

class EventEngine(object):
	"""
	Simple event engine. Register event listeners with the `listen` decorator
	and dispatch events using `dispatch`. Events will be dispatched to all
	listeners who are registered to the event.

	Example:

	>>> ev = EventEngine()
	>>> @ev.listen('run')
	... def runner(script):
	...   print 'Running %s' % (script)
	... 
	>>> ev.dispatch('run', 'foo.scr')
	Running foo.scr
	"""
	def __init__(self, debug=False):
		self.debug = debug
		self.listeners = {}

	def listen(self, event):
		"""
		Decorator for registering a listener to an event. `event` can be any
		object that can be stored as a key in a dict.
		"""
		self.listeners.setdefault(event, [])
		def decorator(fn):
			self.listeners[event].append(fn)
			def new(*args, **kwargs):
				return(fn(*args, **kwargs))
			return(new)
		return(decorator)

	def dispatch(self, event, *args, **kwargs):
		"""
		Dispatch `event` to all the listeners that are registered to it.
		Additional arguments passed to this function are passed to the
		listeners, so they must be declared so that they can handle them.
		"""
		for listener in self.listeners.get(event, []):
			if self.debug:
				sys.stderr.write('Firing \'%s\' event to %s\n' % (event, repr(listener)))
			stop = listener(*args, **kwargs)
			if stop == False:
				break

if __name__ == '__main__':
   import doctest
   doctest.testmod()
