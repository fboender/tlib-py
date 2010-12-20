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

def typed(*d_args, **d_kwargs):
	"""
	Function parameter typing decorator. Raises TypeError if a passed parameter
	is not of the type indicated.

	Example:
	>>> @typed(int, str, list)
	... def my_function(i, s, l):
	...   print i, s, l
	...
	>>> my_function(1, 'one', 1)
	Traceback (most recent call last):
		...
	TypeError: <function my_function at 0x7f232be13320> expects param 2 to be of type 'list'
	"""
	def decorator(fn):
		def new(*args, **kwargs):
			try:
				for i in range(len(args)):
					if type(args[i]) != d_args[i]:
						raise TypeError('%s expects param %i to be of type \'%s\'' % (fn, i, d_args[i].__name__))
			except IndexError, e:
				raise TypeError('%s takes %i arguments; typed() decorator has %i' % (fn, fn.func_code.co_argcount, len(d_args)))
			return(fn(*args, **kwargs))
		return(new)
	return(decorator)

if __name__ == '__main__':
   import doctest
   doctest.testmod(optionflags=doctest.IGNORE_EXCEPTION_DETAIL)
