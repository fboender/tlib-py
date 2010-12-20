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

import optparse
import logging
import os
import sys

class DaemonError(Exception):
	pass

class Daemon:

	"""
	Daemonize the current process (detach it from the console).
	"""

	def __init__(
			self,\
			pidfile=os.path.basename(sys.argv[0])+'.pid',\
			printpid=False,\
			configfile=os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])),os.path.basename(sys.argv[0])+'.ini'),\
			logfile=os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])),os.path.basename(sys.argv[0])+'.log')\
		):
		self.pidfile = pidfile
		self.printpid = printpid
		self.configfile = configfile
		self.logfile = logfile

		# Parse commandline options
		parser = optparse.OptionParser()
		parser.add_option("--start", dest="start", action="store_true", default=True, help="Start Kip (default)")
		parser.add_option("--stop", dest="stop", action="store_true", default=False, help="Stop Kip")
		parser.add_option("--restart", dest="restart", action="store_true", default=False, help="Restart Kip")
		parser.add_option("-V", "--verbose", dest="verbose", action="store_true", default=False, help="Be verbose (show lots of output)")
		parser.add_option("-l", "--log-stdout", dest="log_stdout", action="store_true", default=False, help="Also log to stdout")
		#parser.add_option("-f", "--foreground", dest="foreground", action="store_true", default=False, help="Do not go into daemon mode.")
		(self.arg_options, self.arg_rest) = parser.parse_args()

		# Setup logging
		if self.arg_options.verbose:
			self.loglevel = logging.DEBUG
		else:
			self.loglevel = logging.INFO

		logging.basicConfig(
			level=self.loglevel,
			format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
			filename=self.logfile,
			filemode='a'
		)
		self.log = logging.getLogger('daemon')
		self.log.setLevel(self.loglevel)

		self.log.debug('pidfile = %s' % (self.pidfile))
		self.log.debug('configfile = %s' % (self.configfile))
		self.log.debug('logfile = %s' % (self.logfile))

		if self.arg_options.log_stdout:
			console = logging.StreamHandler()
			formatter = logging.Formatter('[%(levelname)s] %(message)s')
			console.setFormatter(formatter)
			console.setLevel(self.loglevel)
			self.log.addHandler(console)

		if self.arg_options.verbose:
			self.log.debug('We are being verbose')

		# Time to get busy
		if self.arg_options.restart:
			self.restart()
		elif self.arg_options.stop:
			self.stop()
		elif self.arg_options.start:
			self.start()

	def getrunningpid(self):
		pid = None

		try:
			f = file(self.pidfile, 'r')
			pid = int(f.readline())
			f.close()
		except ValueError, e:
			raise DaemonError("Error in pid file `%s`. Aborting.\n" % (self.pidfile))
			#sys.stderr.write("Error in pid file `%s`. Aborting.\n" % (self.pidfile))
			#sys.exit(-1)
		except IOError, e:
			pass

		if pid:
			# Test if the PID is actually running
			try:
				os.kill(pid, 0)
			except OSError:
				pid = None

		return(pid)

	def restart(self):
		self.stop()
		self.start()

	def stop(self):
		self.log.info('Stopping')
		pid = self.getrunningpid()
		if pid:
			try:
				os.kill(pid, 15)
			except OSError, e:
				raise DaemonError('No process with PID %i found. Perhaps the server isn\'t running?\n' % (pid))
		else:
			raise DaemonError('PID file %s not found. Perhaps the server isn\'t running?\n' % (self.pidfile))

		try:
			os.unlink(self.pidfile)
		except OSError, e:
			pass

		raise SystemExit()

	def start(self):
		self.log.info('Starting')
		pid = self.getrunningpid()
		if pid:
			raise DaemonError('PID file found. Process already running? If not, remove PID file: %s\n' % (self.pidfile))

		# Fork a child and end the parent (detach from parent)
		try:
			pid = os.fork()
			if pid > 0:
				sys.exit(0) # End parent
		except OSError, e:
			sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(-2)

		# Change some defaults so the daemon doesn't tie up dirs, etc.
		os.setsid()
		os.umask(0)

		# Fork a child and end parent (so init now owns process)
		try:
			pid = os.fork()
			if pid > 0:
				if self.pidfile:
					try:
						f = file(self.pidfile, 'w')
						f.write(str(pid))
						f.close()
					except IOError, e:
						sys.stderr.write(e + '\n')
						sys.exit(-1)

				if self.printpid:
					sys.stderr.write("PID = " + str(pid) + '\n')
				sys.exit(0) # End parent
		except OSError, e:
			sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(-2)

		# Close STDIN, STDOUT and STDERR so we don't tie up the controlling
		# terminal
		for fd in (0, 1, 2):
			try:
				os.close(fd)
			except OSError:
				pass

		# Reopen the closed file descriptors so other os.open() calls don't
		# accidentally get tied to the stdin etc.
		# FIXME: stderr/stdout to logging
		os.open("/dev/null", os.O_RDWR)	# standard input (0)
		os.dup2(0, 1)			# standard output (1)
		os.dup2(0, 2)			# standard error (2)

if __name__ == "__main__":
	import time

	try:
		daemon = Daemon()
	except DaemonError, e:
		sys.stderr.write('\n'.join(e.args))
		sys.exit(-1)

	while True:
		daemon.log.info('tick')
		time.sleep(2)
