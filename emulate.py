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

import __builtin__
import StringIO
import os

class EmulateError(Exception):
	"""
	Emulation Error. Thrown when a request is made into the emulated system
	which cannot be fullfilled because it is not being emulated.
	"""
	pass

__files = {}

def file(path, contents):
	"""
	Emulate the existance of a file. Overrides os.path.exists(), file() and
	open(). Raises EmulateError if the file has not been registered using this
	function.

	Example:
	>>> file('/spam', 'SPAM SPAM SPAM SPAM')
	>>> import os
	>>> os.path.exists('/spam')
	True
	>>> for line in file('/spam', 'r'):
	...   print line
	SPAM SPAM SPAM SPAM
	"""
	__files[path.rstrip(os.path.sep)] = contents
	os.path.exists = __os_path_exists
	__builtin__.file = __builtins_file
	__builtin__.open = __builtins_file

def __os_path_exists(path):
	if path.rstrip(os.path.sep) in __files:
		return True
	else:
		raise EmulationError('%s: No such file or directory' % (path))

def __builtins_file(name, mode='a', buffering=0):
	print name
	print __files
	if name in __files:
		f = StringIO.StringIO()
		f.write(__files[name])
		f.seek(0)
		return(f)
	else:
		raise EmulateError('%s: No such file or directory' % (name))
