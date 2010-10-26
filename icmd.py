#!/usr/bin/python

"""
ICmd is a wrapper library for easily creating interactive commandline programs.
You simply create a class that inherits from the ICmdBase class and create a
new ICmd instance with that class.

ICmd will automatically use readline if it is available, giving you a history
and tab-completion of commands. The ICmd class will get input from the user and
then run methods on the root class you passed to its constructor.

Example:

	class ICmdTest(ICmdBase):
		def load(self, fname):
			self.fname = fname
			print "Loading %s" % (self.fname)

		def save(self):
			fname = getattr(self, 'fname', None)
			print "Saving %s" % (fname)

		def test(self, required, optional='optional'):
			logging.info("Test: required=%s, optional=%s" % (required, optional))

	icmd = ICmd(ICmdTest)
	icmd.run()
"""

import sys
import os
import inspect
import logging
try:
	import readlin
except ImportError:
	pass

class ICmdBase(object):
	"""
	Base class for ICmd commandline classes. Inherit from this class to get
	default commands in your commandline application.
	"""
	def __init__(self, helptext_prefix = '', helptext_suffix = ''):
		self.helptext_prefix = helptext_prefix
		self.helptext_suffix = helptext_suffix

	def help(self, command=None):
		"""
		Display help
		Displays all available commands or specific help for COMMAND if given.
		"""
		if command:
			# Display command-specific help
			try:
				func = getattr(self, command)
			except AttributeError, e:
				raise ICmdError(1, "No such command: '%s'. Type 'help [command]' for help." % (command))

			if not command.startswith('_') and callable(func):
				help = self._help_getspecifics(command)
				print "%s: %s" % (command, help[0])
				print "Usage: %s\n" % (help[2])
				print "  %s\n" % (help[1])
		else:
			# Display all available commands
			print self.helptext_prefix
			for cmd in dir(self):
				if not cmd.startswith('_') and callable(getattr(self, cmd)):
					help = self._help_getspecifics(cmd)
					print '  %s: %s' % (cmd, help[0])
			print self.helptext_suffix

	def _help_getspecifics(self, command):
		help_short = ''
		help_desc = ''
		help_usage = ''

		# Get short and full descriptions from the function's docstring.
		func = getattr(self, command)
		if func.__doc__:
			doc = [l.strip() for l in func.__doc__.strip().splitlines()]
			if len(doc) == 1:
				help_short = doc[0]
			else:
				help_short, help_desc = doc[0], doc[1]

		# Get usage from the parameters
		args = inspect.getargspec(func)
		parcnt_max = len(args.args) - 1
		parcnt_min = len(args.args) - 1 - len(args.defaults or '')
		help_usage = command
		for i in range(1, len(args.args)):
			if i <= parcnt_min:
				help_usage += " [%s]" % (args.args[i])
			else:
				help_usage += " <%s>" % (args.args[i])

		return([help_short, help_desc, help_usage])

	def quit(self):
		"""
		Exit the program.
		"""
		raise SystemExit()

	exit = quit

class ICmdError(Exception):
	pass

class ICmd(object):
	"""
	Interactive/Batch Commandline interface. Given a class that overloads the
	ICmdBase class, provide an interactive commandline to control that class.
	"""

	def __init__(self, rootclass, prompt='> ', welcometext='Type \'help\' for help.', helptext_prefix='The following commands are available: (type \'help <command>\' for details)\n', helptext_suffix='', silent=False):
		"""
		Create a new interactive commandline interface to rootclass by creating
		an instance of rootclass (your class must derive from ICmdBase). Use
		ICmd.run() or run_once() to start the commandline client.
		"""
		self.rootclass = rootclass
		self.prompt = prompt
		self.welcometext = welcometext
		self.silent = silent
		self.instclass = self.rootclass(helptext_prefix, helptext_suffix)

		# Initialize readline, but only if we were able to load the module.
		if 'readline' in sys.modules:
			logging.info("Using readline")
			self.histfile = os.path.join(os.environ["HOME"], ".mcinvedit")
			try:
				readline.read_history_file(self.histfile)
			except IOError:
				pass
			logging.info("Setting readline completer")
			readline.set_completer(self._completer)
			readline.parse_and_bind("tab: complete")

		if not self.silent:
			print welcometext

	def dispatch(self, cmd, params=[]):
		"""
		Run `cmd` on the rootclass. `cmd` must be an existing callable in
		rootclass. Raises ICmdErrors in case of problems with the command (no
		such command, too many/few parameters).
		"""
		logging.info("Dispatching %s %s" % (cmd, str(params)))
		try:
			func = getattr(self.instclass, cmd)
		except AttributeError, e:
			raise ICmdError(1, "No such command: '%s'. Type 'help [command]' for help." % (cmd))

		# Introspect how many arguments the function takes and how many the
		# user gave.
		args = inspect.getargspec(func)

		parcnt_given = len(params)
		parcnt_max = len(args.args) - 1
		parcnt_min = len(args.args) - 1 - len(args.defaults or '')
		logging.info("dispatch: params: given: %i, min: %i, max: %i" % (parcnt_given, parcnt_min, parcnt_max))

		if parcnt_given < parcnt_min:
			raise ICmdError(2, 'Not enough parameters given')
		elif parcnt_given > parcnt_max:
			raise ICmdError(3, 'Too many parameters given')

		return(func(*params))

	def _completer(self, text, state):
		"""
		Readline completer. Scans the Command object instance for member
		functions that match. Returns the next possible completion requested
		(state).
		"""
		logging.info("Completing '%s' '%s'" % (text, state))
		w = [cmd for cmd in dir(self.instclass) if cmd.startswith(text) and not cmd.startswith('_') and callable(getattr(self.instclass, cmd))]
		try:
			return(w[state])
		except IndexError:
			return None

	def run_once(self):
		"""
		Ask the user for a single line of input and run that command. Returns
		the returned result of the command callable (i.e. the return value of
		the function in rootclass).
		"""
		input = raw_input(self.prompt).split()
		if input:
			cmd = input.pop(0)
			params = input
			return(self.dispatch(cmd, params))
		else:
			return(False)

	def run(self, catcherrors=True):
		"""
		Continually ask the user for lines of input and run those commands.
		Catches all ICmdErrors and displays those errors. Catches
		KeyboardInterrupt and SystemExit exceptions in order to clean up
		readline.
		"""
		try:
			while True:
				if catcherrors:
					try:
						self.run_once()
					except ICmdError, e:
						print e.args[1]
						logging.info("ICmd.run intercepted an error: %s" % (e))
				else:
					self.run_once()
		except (SystemExit, KeyboardInterrupt):
			if 'readline' in sys.modules:
				logging.info("Writing readline command history")
				readline.write_history_file(self.histfile)

if __name__ == "__main__":
	class ICmdTest(ICmdBase):
		def load(self, fname):
			self.fname = fname
			print "Loading %s" % (self.fname)

		def save(self):
			fname = getattr(self, 'fname', None)
			print "Saving %s" % (fname)

		def test(self, required, optional='optional'):
			logging.info("Test: required=%s, optional=%s" % (required, optional))

	#logging.getLogger().level = logging.INFO
	icmd = ICmd(ICmdTest)
	icmd.run()

	icmd.dispatch('load', ['foo'])
	icmd.dispatch('save')
