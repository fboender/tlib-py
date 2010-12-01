#!/usr/bin/python

import plugin

class TestPlugin(plugin.Plugin):
	def __init__(self):
		super(TestPlugin, self).__init__()
		self.logger.debug('Hello world!')

	def event_start(self):
		self.logger.debug('event_start called')

__DESCRIPTION__ = "Test if collisions between plugins/python don't happen"
__AUTHOR__ = "Ferry Boender"
__VERSION__ = (0, 1)
__MAIN__ = TestPlugin()
