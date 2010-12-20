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
Simple Database layer that can return rows as dicts.
"""

import sys

class PDOError(Exception):
	def __init__(self, message, code):
		self.code = code
		Exception.__init__(self, message)

class PDO:
	debug = False

	def __init__(self, engine, **kwargs):
		self.engine = engine

		try:
			if engine == 'sqlite3':
				self.module = __import__('sqlite3')
				self.connection = self.module.connect(kwargs['db'])
			elif engine == 'MySQLdb':
				self.module = __import__('MySQLdb')
				self.connection = self.module.connect(**kwargs)
			else:
				raise PDOError('Unsupported engine \'%s\'' % (engine), 1)
		except KeyError, e:
			raise PDOError('Missing parameter for engine connect: %s' % (e.message), 2)

	def execute(self, query, *args, **kwargs):
		cursor = PDOCursor(self.connection.cursor())
		if self.debug:
			sys.stderr.write('%s\n' % query)
			for v in args:
				sys.stderr.write('%s\n' % str(v))
			for k, v in kwargs:
				sys.stderr.write('%s:%s\n' % (k, str(v)))
		cursor.execute(query, *args, **kwargs)
		return(cursor)

	def find(self, table, **kwargs):
		qry_where = ' AND '.join(['%s=:%s' % (key, key) for key in kwargs.keys()])
		query = "SELECT * FROM `%s` WHERE %s" % (table, qry_where)
		return(self.execute(query, kwargs))

	def commit(self):
		self.connection.commit()

class PDOCursor:

	def __init__(self, cursor):
		self.cursor = cursor

	def __getattr__(self, x):
		return(getattr(self.cursor, x))

	def fetch(self):
		row = self.cursor.fetchone()
		if row:
			return(dict([(coldesc[0], row[pos]) for pos, coldesc in enumerate(self.description)]))
		else:
			return None
		
	def __iter__(self):
		while True:
			row = self.fetch()
			if not row:
				break
			yield(row)

	def __str__(self):
		return('<PDOCursor object at %s>' % (id(self)))

if __name__ == "__main__":
	# Self tests
	import os

	#try:
	#	os.unlink('pdo.db')
	#except OSError:
	#	pass

	#try:
	#	pdo = PDO('unknownengine')
	#except PDOError, e:
	#	if e.code == 1:
	#		pass
	#	else:
	#		raise

	#try:
	#	pdo = PDO('sqlite3')
	#except PDOError, e:
	#	if e.code == 2:
	#		pass
	#	else:
	#		raise

	pdo = PDO('sqlite3', db='pdo.db')
	#res = pdo.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name VARCHAR(100), value INTEGER)')
	#res = pdo.execute('INSERT INTO test VALUES (NULL, :name, :value)', {'name':'foo', 'value':101})
	#pdo.commit()

	res1 = pdo.execute('SELECT id FROM test')
	print res1
	for row in res1:
		print row
