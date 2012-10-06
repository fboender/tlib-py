# Copyright (c) 2010-2012 Ferry Boender
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

ACTION_START = 1
ACTION_STOP = 2
ACTION_RESTART = 3

class DaemonError(Exception):
    pass

class Daemon:
    """
    Daemonize the current process (detach it from the console).
    """

    def __init__(
            self, pidfile=None, printpid=True, configfiles=None, logfile=None,
            loglevel=logging.INFO, log_stdout=False, foreground=False
        ):
        self.printpid = printpid
        self.loglevel = loglevel
        self.log_stdout = log_stdout
        self.foreground = foreground
        self.basepath = os.path.realpath(os.path.dirname(sys.argv[0]))
        self.basename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        if pidfile:
            self.pidfile = pidfile
        else:
            if os.geteuid() == 0:
                self.pidfile = os.path.join('/var/run', self.basename+'.pid')
            else:
                self.pidfile = os.path.join(self.basepath, self.basename+'.pid')
        if configfiles:
            self.configfiles = configfiles
        else:
            self.configfiles = [
                os.path.join(self.basepath, self.basename+'.conf'),
                os.path.join(os.getenv('HOME'),'.'+self.basename, self.basename+'.conf'),
                os.path.join('/etc', self.basename, self.basename+'.conf'),
            ]
        if logfile:
            self.logfile = logfile
        else:
            if os.geteuid() == 0:
                self.logfile = os.path.join('/var/log/', self.basename+'.log')
            else:
                self.logfile = os.path.join(self.basepath, self.basename+'.log')

        logging.basicConfig(
            level=self.loglevel,
            format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
            filename=self.logfile,
            filemode='a'
        )
        self.log = logging.getLogger(self.basename)
        self.log.setLevel(self.loglevel)

        if self.log_stdout:
            console = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            console.setFormatter(formatter)
            console.setLevel(self.loglevel)
            self.log.addHandler(console)

        self.log.info('pidfile = %s' % (self.pidfile))
        self.log.info('loglevel = %s' % (self.loglevel))
        self.log.info('configfile = %s' % (str(self.configfiles)))
        self.log.info('logfile = %s' % (self.logfile))

    def getrunningpid(self):
        pid = None

        try:
            f = file(self.pidfile, 'r')
            pid = int(f.readline())
            f.close()
        except ValueError, e:
            raise DaemonError("Error in pid file `%s`. Aborting.\n" % (self.pidfile))
        except IOError, e:
            pass

        if pid:
            # Test if the PID is actually running
            try:
                os.kill(pid, 0)
            except OSError:
                pid = None

        return(pid)

    def action(self, action):
        if action == ACTION_RESTART:
            self.stop()
            self.start()
        elif action == ACTION_STOP:
            self.stop()
            raise SystemExit()
        elif action == ACTION_START:
            self.start()


    def restart(self):
        self.log.debug('Restarting')
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
                    self.log.info("PID: %s" % (pid))
                    sys.stdout.write("PID = " + str(pid) + '\n')
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
        os.open("/dev/null", os.O_RDWR)    # standard input (0)
        os.dup2(0, 1)            # standard output (1)
        os.dup2(0, 2)            # standard error (2)

if __name__ == "__main__":
    import time

    parser = optparse.OptionParser()
    parser.set_usage(sys.argv[0] + " [option]")

    parser.add_option("--start", dest="action", action="store_const", const=ACTION_START, default=True, help="Start daemon(default)")
    parser.add_option("--stop", dest="action", action="store_const", const=ACTION_STOP, default=False, help="Stop daemon")
    parser.add_option("--restart", dest="action", action="store_const", const=ACTION_RESTART, default=False, help="Restart daemon")
    parser.add_option("-d", "--debug", dest="debug", type="int", action="store", default=30, help="Debug level (0-50)")

    (options, args) = parser.parse_args()
    options.debug = 50 - options.debug # invert debug lvl: 0 = low, 50 = high

    try:
        daemon = Daemon(loglevel=options.debug)
        daemon.action(options.action)
    except DaemonError, e:
        sys.stderr.write('\n'.join(e.args))
        sys.exit(-1)

    while True:
        daemon.log.debug('tick')
        time.sleep(1)
