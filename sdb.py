import sys
import shlex

"""
The graph module allows you to use Graph data structures. A graph has nodes and
edges which connect the various nodes. A range of operations can be performed
on the data structures such as walking the graph, doing dependency resolution
and finding the shortest path.

Example:

>>> g = Graph()
>>> g.add_node('php')
>>> g.add_node('apache')
>>> g.add_node('pear')
>>> g.add_node('wordpress')
>>> g.add_node('genshi')
>>> g.add_edge('wordpress', 'pear')
>>> g.add_edge('genshi', 'wordpress')
>>> g.add_edge('pear', 'php')
>>> g.add_edge('php', 'apache')
>>> g.resolve('wordpress')
['apache', 'php', 'pear', 'wordpress']
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

