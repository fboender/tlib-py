#!/usr/bin/python

# TODO: 
#  - Non-blocking main server thread? (listen blocks currently). 
#  - Exception KeyboardInterrupt in <module 'threading' from '/usr/lib/python2.6/threading.pyc'> ignored


import logging
import socket
import select
import ssl
import threading

"""
Simple multithreaded full-duplex request/response SSL server.

The SSLServer class is the main server class. It waits for and accepts
connections, verifies the SSL certificates on those connections and fires off a
thread by instantiating the connection handler (SSLConnection).

You should create a new class which inherits from SSLConnection and implements the
SSLConnection.process_data() method.

Example:
	class MySSLConnection(SSLConnection):
		def process_data(self, request):
			# Custom data handler.
			response = []
			for line in request.splitlines():
				parts = line.split()
				if parts:
					try:
						f = getattr(self, '_cmd_%s' % (parts[0].lower()))
						try:
							r = f(*parts[1:])
							if r:
								response.append(r)
							else:
								response.append('OK')
						except (Exception) as e:
							response.append('ERROR %s' % (e))
					except (AttributeError) as e:
						response.append('ERROR 1 Unknown command: %s' % (parts[0]))
			return(str('\n').join(response))

		def _cmd_ping(self, *args):
			return('PONG')

		def _cmd_mirror(self, *args):
			# Return arguments we received
			return(str(' '.join(args)))

	sslserver = SSLServer(connection_handler=MySSLConnection)
	sslserver.run()

Creating a server certificate:

	$ openssl req -new -x509 -days 365 -nodes -out client.pem -keyout client.pem

"""

class SSLConnection(threading.Thread):
	"""
	Threaded SSL connection handler. Clients should inherit from this object
	and implement the `process_data()` method to handle data.
	"""
	def __init__(self, sock, ssl_sock, fromaddr):
		super(SSLConnection, self).__init__()

		self.sock = sock
		self.ssl_sock = ssl_sock
		self.fromaddr = fromaddr
		self.timeout = 5
		self.bufsize = 4096
		self.max_bufsize = 2 ** 20 # About 1 Mb
		self.logger = logging.getLogger('SSLCONNECTION')
		self.logger.debug("Processing connection from %s:%i" % (self.fromaddr[0], self.fromaddr[1]))

	def run(self):
		"""
		Start the thread.
		"""
		self.process_forever()

	def process_forever(self):
		"""
		Keep communicating with the client until `process_once()` returns a
		value that does not evaluate to True.
		"""
		while True:
			result = self.process_once()
			if not result:
				# process_once indicates we should stop processing
				return result

	def process_once(self):
		"""
		Process a single receive/send cycle. Read data from the client and
		dispatch it to `self.process_data()`. If `self.process_data` returns a
		value that evaluates to True (non-empty string), send it to the client
		and return True (so `process_forever()` keeps running and starts
		reading form the client again after the response). Otherwise, or if the
		client has gone away, return False.
		"""
		# Read request
		self.logger.debug("Waiting for data from client")
		i, o, e = select.select([self.ssl_sock, ], [], [], self.timeout)
		self.logger.debug("sockstatus: %s %s %s" % (str(i), str(o), str(e)))

		if self.ssl_sock in i:
			# Socket is ready for reading
			buf = ''
			# Keep reading from the socket until the maximum buffersize is
			# reached or if the client goes away or if the client is done
			# sending data.
			#while len(buf) < self.max_bufsize:
			while True:
				d = self.ssl_sock.recv(self.bufsize)
				self.logger.debug('recv: %i bytes\n%s' % (len(d), d))
				buf += d
				if len(buf) >= self.max_bufsize:
					# Maximum buffer filled. Stop processing
					self.logger.debug("Maximum buffer size reached")
					return(False)
				if len(d) == 0:
					# No data, client must have gone away. Stop reading data
					self.logger.debug("Client gone?")
					return(False)
				elif len(d) < self.bufsize:
					# Stop reading when there's no more data.  Dispatch
					# received data to the process_data method and send the
					# result to the client. Return the result to the caller so
					# they know if we need to keep reading for commands.
					result = self.process_data(buf)
					if result:
						self.logger.debug("Sending %s" % (result))
						self.ssl_sock.send(result)
					return(result)
		if self.ssl_sock in e:
			# Error
			raise SystemExit('sockerr')

		return(True)

	def process_data(self, buf):
		"""
		Dummy recieved data processing function. Override this in your class
		which inherits from SSLConnection. Return False to stop communicating
		with the client or a string to send back to the client as a response
		and continue communicating with the client.
		"""
		return(False)

class SSLServer(object):
	"""
	Simple multi-threaded, full-duplex SSL Server with client certificate
	verification.

	Example:

		class MySSLConnection(SSLConnection):
			def process_data(self, data):
				print "received:", data
				print "sending: foo"
				return('foo')

		sslserver = SSLServer(connection_handler=MySSLConnection)
		sslserver.run()
	"""
	def __init__(self, bind_address='127.0.0.1', bind_port=8080,
			server_cert='server.pem', verify_clients=True,
			client_certs='clients.pem', connection_handler=SSLConnection):
		"""
		Create a new SSL Server object. `bind_address` is the IP to listen on
		(default 127.0.0.1), `bind_port` the port (default:8080). `server_cert`
		is the path to the server certificate (.pem file).

		If `verify_clients` is True (default: True), the SSL server will
		require clients to authenticate themselves with a certificate which
		should be present in the file to which `client_certs` points.
		`client_certs` file contains a concatenated list of normal certificate
		files (see module documentation on how to create certificates).

		`connection_handler` is a non-instantiated class that inherits from
		SSLConnection and implements SSLConnection.process_data().
		"""
		self.bind_address = bind_address
		self.bind_port = bind_port
		self.server_cert = server_cert
		self.verify_clients = verify_clients
		self.client_certs = client_certs
		self.connection_handler = connection_handler
		self.logger = logging.getLogger('SSLSERVER')
		self.connections = [] # List of open connections

	def run(self):
		"""
		Run the SSL server. The server will start accepting connections and
		dispatch them to the connection handler. This function will block.
		"""
		sock = socket.socket()
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind((self.bind_address, self.bind_port))
		self.listen(sock)

	def listen(self, sock):
		"""
		Listen for incoming connections, wrap them in a SSL layer, creates a
		new thread by instantiating `self.connection_handler` object (of type
		SSLConnection) and calls the `run()` method on it. When the thread is
		done, it is cleaned up after about a second.
		"""
		self.logger.info("Listening on %s:%i" % (self.bind_address, self.bind_port))
		sock.listen(5)

		while True:
			# Check for incoming connections
			i, o, e = select.select([sock, ], [], [], 1)

			# Clean up finished SSLConnections.
			# FIXME: Maybe this should run in its own thread?
			for i in range(len(self.connections)-1, -1, -1):
				conn = self.connections[i-1]
				if not conn.is_alive():
					self.logger.info("Disconnecting client: %s:%i" % (conn.fromaddr[0], conn.fromaddr[1]))
					conn.ssl_sock.close()
					conn.sock.close()
					self.connections.pop(i)

			# If the socket indicates a client is there, accept the connection,
			# wrap the socket in an SSL layer and spawn a thread to handle the
			# connection.
			if i:
				commsock, fromaddr = sock.accept()
				self.logger.info("Client connected: %s:%i" % (fromaddr[0], fromaddr[1]))

				try:
					commsock_ssl = ssl.wrap_socket(commsock, server_side=True, certfile=self.server_cert, cert_reqs=ssl.CERT_REQUIRED, ca_certs=self.client_certs)
					self.logger.debug("Forking thread")
					ssl_conn = self.connection_handler(commsock, commsock_ssl, fromaddr)
					self.connections.append(ssl_conn)
					ssl_conn.start()
					self.logger.debug("Continuing listening")
					continue
				except ssl.SSLError, e:
					self.logger.error("SSL Error: %s" % (e))
				except socket.error, e:
					self.logger.error("Socket Error: %s" % (e))

#logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
