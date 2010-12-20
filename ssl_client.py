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

# Todo:
# Traceback (most recent call last):
#   File "./client.py", line 92, in <module>
#     client = SSLClient(client_cert='client1.pem', server_cert='server.pem')
#   File "./client.py", line 38, in __init__
#     self.ssl_sock.connect((self.conn_address, self.conn_port))
#   File "/usr/lib/python2.6/ssl.py", line 304, in connect
#     socket.connect(self, addr)
#   File "<string>", line 1, in connect
# socket.error: [Errno 111] Connection refused

__VERSION__ = (0, 1)

"""
Example:
	client = SSLClient(client_cert='client.pem', server_cert='server.pem')

	response = client.send('PING')
	print response
	response = client.send('MIRROR abc def TEST')
	print response

	client.close()

Creating a client certificate:

	$ openssl req -new -x509 -days 365 -nodes -out client.pem -keyout client.pem

"""
import socket
import logging
import ssl
import select
import time

class SSLClientError(Exception):
	errnos = {
		1: "Client certificate not found",
		2: "Server certificate not found",
		3: "Client certificate invalid",
		4: "Server certificate invalid",
	}

	def __init__(self, errno, *args):
		self.errno = errno
		self.args = args

	def __str__(self):
		return('%s: %s' % (self.errnos[self.errno], self.args))

class SSLClient(object):
	"""
	Simple SSL client class. Creates a connection when you instantiate the
	class, after which you can send data to the server using the send() method.
	That method will return whatever the server returned as a response.
	"""
	def __init__(self, conn_address='127.0.0.1', conn_port=8080,
			client_cert='client.pem', verify_server=True,
			server_cert='server.pem'):
		"""
		Creates a new SSLClient class. `conn_address` is the IP address to
		connect to, `conn_port` the port. `client_cert` is the path to the
		client certificate (not required if the server doesn't verify clients).
		`server_cert` is the path to the server certificate (not required if
		verify_server if False). `verify_server` tells the client that the
		server's certificate must match the server_cert.
		"""
		self.conn_address = conn_address
		self.conn_port = conn_port
		self.client_cert = client_cert
		self.server_cert = server_cert
		self.verify_server = verify_server
		self.bufsize = 128
		self.logger = logging.getLogger('SSLCLIENT')

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.ssl_sock = ssl.wrap_socket(self.sock, certfile=self.client_cert,
				ca_certs=self.server_cert, cert_reqs=ssl.CERT_REQUIRED)
			self.ssl_sock.connect((self.conn_address, self.conn_port))
		except (ssl.SSLError) as (errno, strerror):
			if errno == 336265218:
				raise SSLClientError(1, self.client_cert)
			elif errno == 185090050:
				raise SSLClientError(2, self.server_cert)
			elif errno == 336265225:
				raise SSLClientError(3, self.client_cert)
			elif errno == 185090057:
				raise SSLClientError(4, self.server_cert)
			else:
				raise

		toaddr = self.ssl_sock.getpeername()
		self.logger.debug("Connected to %s:%i" % (toaddr[0], toaddr[1]))

	def send(self, data):
		"""
		Send `data` to the server. Returns the reply.
		"""
		self.logger.debug("Sending: %s" % (data))
		self.ssl_sock.write(data)

		buf = ''
		while True:
			d = self.ssl_sock.recv(self.bufsize)
			self.logger.debug("recv: %i bytes\n%s" % (len(d), d))
			buf += d
			if len(d) == 0:
				# No data from server.Must have gone away. Stop reading data
				return(False)
			elif len(d) < self.bufsize:
				# Server is done sending data.
				return(buf)

		return(buf)

	def close(self):
		"""
		Close the connection.
		"""
		self.ssl_sock.close()
		self.sock.close()

#logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")

