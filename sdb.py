import sys
import shlex

"""
"""

class SDB(object):
	def __init__(self, colnames, coltypes=None):
		self.colnames = colnames
		self.coltypes = coltypes
		self.rows = []

	def read_file(self, fname, sep="\t", errors=True):
		for line in file(fname, 'r'):
			cols = line.strip().split(sep)

			# Does the line has the expected number of columns?
			if len(cols) != len(self.colnames):
				if errors:
					raise SDBError('Invalid number of cols in line "%s"' % (line))
				else:
					continue # Skip this line

			self.rows.append(cols)
		
	def query(self, fields, query):
		lex = shlex.shlex(query)
		token_queue = []
		for token in lex:
			if token.lower() == '=':
				field = token_queue.pop()
				value = token.get_token()

				print "IS"
			else:
				token_queue.append(token)
				
s = SDB(('username', 'passwd', 'uid', 'gid', 'fullname', 'homedir', 'shell'))
s.read_file('/etc/passwd', sep=':')
s.query(('username', 'uid'), 'shell = "/bin/false"')

