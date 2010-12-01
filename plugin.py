#!/usr/bin/python

#TODO: 
# - Event dispatching should be done in seperate threads. 

"""

Example plugin:

	--------------------------------------------------
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
	--------------------------------------------------

Example program for above plugin:

	--------------------------------------------------
	import plugin

	logging.basicConfig(level=logging.DEBUG)

	pm = PluginManager('plugins')
	pm.trigger('start')
	for plugin, result in pm.trigger('load', 'param1'):
		logging.debug("Plugin '%s' returned: %s" % (plugin, result))
	pm.reload_all()
	--------------------------------------------------
"""

import sys
import os
import logging

class PluginError(object):
	pass

class Plugin(object):
	"""
	Base class for plugins.
	"""
	def __init__(self):
		# Create a logger instance for the plugin
		pluginname = self.__module__
		self.logger = logging.getLogger('plugin_%s' % (pluginname))
		self.logger.level = logging.getLogger().level

class PluginManager(object):
	def __init__(self, path):
		"""
		Create a new plugin manager. Plugins will be loaded from `path`, which
		may be an absolute or relative path.
		"""
		# Create a logger instance for the pluginmanager
		self.logger = logging.getLogger('pluginmanager')
		self.logger.level = logging.getLogger().level

		self.plugins = {}
		self.events = {}

		if path.startswith('/'):
			# Absolute path
			self.path = path
		else:
			# Path is relative to binary called.
			self.path = os.path.join(
				os.path.dirname(os.path.abspath(sys.argv[0])),
				path
			)

		self.load_all()

	def load_all(self, reload_=False):
		"""
		Load all plugins found in self.path. A file in that directory qualifies
		as a plugin is it ends with .py.
		"""
		self.logger.debug("Loading plugins from path '%s'" % (self.path))
		# Try to load all the Python files in self.path as plugins.
		for fname in os.listdir(self.path):
			root, ext = os.path.splitext(fname)
			if ext == '.py':
				self.load(root, reload_)

	def load(self, name, reload_=False):
		"""
		Load a plugin by the name of 'name'. If reload_ is True, the plugin is
		reloaded instead. Do NOT call this is the plugin isn't yet loaded.
		"""
		sys.path.insert(0, self.path)
		try:
			# Load the plugin as a Python module
			if reload_:
				self.logger.debug("Reloading plugin '%s'" % (name))
				module = reload(sys.modules[name])
			else:
				self.logger.debug("Loading plugin '%s'" % (name))
				module = __import__(name)
			plugin = {
				'module': module,
				'description': module.__DESCRIPTION__,
				'author': module.__AUTHOR__,
				'version': module.__VERSION__,
				'main': module.__MAIN__,
			}
			self.plugins[name] = plugin
		finally:
			sys.path.pop(0)

	def unload_all(self):
		"""
		Unload all plugins.
		"""
		for name in self.plugins.keys():
			self.logger.debug("Unloading plugin '%s'" % (name))
			self.unload(name)

	def reload_all(self):
		"""
		Reload all plugins.
		"""
		self.logger.debug("Reloading all plugins")
		self.unload_all()
		self.load_all(reload_=True)

	def unload(self, name):
		"""
		Unload the plugin with name 'plugin'.
		"""
		try:
			self.plugins.pop(name)
		except KeyError:
			pass

	def reload(self, name):
		"""
		Reload the plugin with name 'plugin'.
		"""
		self.unload(name)
		self.load(name, reload_=True)

	def dispatch(self, plugin, event, *args, **kwargs):
		"""
		Dispatch `event` (string) to a loaded plugin. Scans the plugin for a
		method that starts with 'event_' and matches the event given. Passes
		any parameters passed to this function along to the event handlers.
		Returns a tuple containing (plugin name, return response) or None if
		the plugin has no event `event`.
		"""
		plugininst = self.plugins[plugin]['main']
		for prop in dir(plugininst):
			attr = getattr(plugininst, prop)
			if callable(attr) and prop.startswith('event_%s' % (event)):
				self.logger.debug("Dispatching event '%s' to plugin '%s'" % (event, plugin))
				result = attr(*args, **kwargs)
				self.logger.debug("Plugin '%s' responded to event '%s' with: %s" % (plugin, event, result))
				return ( (attr(*args, **kwargs), ) )
		return(None)

	def dispatch_all(self, event, *args, **kwargs):
		"""
		Dispatch `event` (string) to all the loaded plugins. Passes any
		parameters passed to this function along to the event handlers. Returns
		a list of tuples containing (plugin name, return response), for each
		plugin which responded to `event`.
		"""
		self.logger.debug("Dispatching event '%s'" % (event))
		results = []
		for name, plugin in self.plugins.items():
			result = self.dispatch(name, event, *args, **kwargs)
			if result != None:
				results.append( (name, result) )
		return(results)

	def trigger(self, event, *args, **kwargs):
		"""
		Alias for self.dispatch_all
		"""
		return(self.dispatch_all(event, *args, **kwargs))

if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	pm = PluginManager('plugins')
	pm.trigger('start')
	for plugin, result in pm.trigger('load', 'param1'):
		logging.debug("Plugin '%s' returned: %s" % (plugin, result))
	pm.reload_all()
	pm.trigger('start')
	pm.reload('test_basic')
	pm.trigger('start')
