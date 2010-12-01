#!/usr/bin/python

import plugin
import os
import tempfile

class FilePlugin(plugin.Plugin):
	def event_create(self, fname):
		# Normalize filename
		filename = os.path.basename(filename)
		f = file(os.path.join(tempfile.gettempdir(), filename), 'w')
		f.write('test')
		f.close()

	def read(self, fname):
		filename = os.path.basename(filename)
		f = file(os.path.join(tempfile.gettempdir(), filename), 'r')
		c = f.readlines()
		f.close()
		return(c)

	def count(self, fhandle):
		cnt = 0
		for b in fhandle.read(1):
			cnt += 1
		return(cnt)

__DESCRIPTION__ = "Do operations on files."
__AUTHOR__ = "Ferry Boender"
__VERSION__ = (0, 1)
__MAIN__ = FilePlugin()
