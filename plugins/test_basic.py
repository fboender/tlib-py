#!/usr/bin/python

import plugin

class TestPlugin(plugin.Plugin):
	def event_start(self):
		self.logger.debug('event_start called')

	def event_load(self, name):
		self.logger.debug('loading %s' % (name))
		return(name)

__DESCRIPTION__ = "Basic plugin"
__AUTHOR__ = "Ferry Boender"
__VERSION__ = (0, 1)
__MAIN__ = TestPlugin()
