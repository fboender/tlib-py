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

__cache = {} # Global cache

def fncache(fn):
   """
   Function caching decorator. Keeps a cache of the return value of a function
   and serves from cache on consecutive calls to the function. 
   
   Cache keys are computed from a hash of the function name and the parameters
   (this differentiates between instances through the 'self' param). Only
   works if parameters have a unique repr() (almost everything).

   Example:

   >>> @fncache
   ... def greenham(a, b=2, c=3):
   ...   print 'CACHE MISS'
   ...   return('I like turtles')
   ... 
   >>> print greenham(1)           # Cache miss
   CACHE MISS
   I like turtles
   >>> print greenham(1)           # Cache hit
   I like turtles
   >>> print greenham(1, 2, 3)     # Cache miss (even though default params)
   CACHE MISS
   I like turtles
   >>> print greenham(2, 2, ['a']) # Cache miss
   CACHE MISS
   I like turtles
   >>> print greenham(2, 2, ['b']) # Cache miss
   CACHE MISS
   I like turtles
   >>> print greenham(2, 2, ['a']) # Cache hit
   I like turtles
   """
   def new(*args, **kwargs):
      h = hash(repr(fn) + repr(args) + repr(kwargs))
      if not h in __cache:
         __cache[h] = fn(*args, **kwargs)
      return(__cache[h])
   new.__doc__ = "%s %s" % (fn.__doc__, "(cached)")
   return(new)

if __name__ == '__main__':
   import doctest
   doctest.testmod()
