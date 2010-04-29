#!/usr/bin/python

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
