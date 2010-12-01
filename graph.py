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

import sys

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

class Graph(object):
	def __init__(self):
		self.nodes = {} # Stores the nodes as keys and their edges as values.

	def add_node(self, node, edges=[]):
		self.nodes[node] = []
		for edge in edges:
			if not edge in self.nodes:
				raise IndexError('No such node: %s' % (repr(edge)))
			self.nodes[node].append(edge)

	def add_edge(self, node, edge):
		self.nodes[node].append(edge)

	def walk(self, callback):
		"""
		Walk through all the nodes in the graph. Order is unpredictable. Also
		walks through unconnected nodes.
		"""
		for node in self.nodes:
			if callback(node, self.nodes[node]) == False:
				return(node)

	def find(self, startnode, findnode):
		"""
		Find a (not necessarly the shortest) path from node `startnode` to
		`findnode`. Returns a list of nodes that denote the path from
		(including) `startnode` to `findnode`.
		"""
		nodes = [startnode]
		visited = []

		while nodes:
			node = nodes.pop(0)
			if node in visited:
				# Skip already visited nodes to prevent circular references.
				continue
			visited.append(node)
			if node == findnode:
				return(visited)
			if self.nodes[node]:
				for edge in self.nodes[node]:
					nodes.append(edge)
	
	def resolve(self, node, resolved=None, unresolved=None):
		"""
		Given that each edge is a dependency for a node, return all the nodes
		required to resolve `node`, in the correct order.
		"""
		if resolved == None:
			resolved = []
		if unresolved == None:
			unresolved = []

		if node in unresolved:
			raise Exception('Circular reference detected: %s %s' % (node, unresolved))
		else:
			unresolved.append(node)

		for edge in self.nodes[node]:
			self.resolve(edge, resolved, unresolved)

		unresolved.remove(node)
		resolved.append(node)

		return(resolved)
