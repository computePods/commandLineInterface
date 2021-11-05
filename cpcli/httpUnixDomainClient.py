"""Subclass the standard http.client.HTTPConnection class to allow
connections to Unix domain sockets. """

import os
import socket
import sys

from http.client import HTTPConnection

class HTTPUnixDomainConnection(HTTPConnection) :
  """Subclass the standard http.client.HTTPConnection class to allow
  connections to Unix domain sockets. """

  def __init__(self, socketPath, **kwargs) :
    super().__init__("localhost", **kwargs)
    self.socketPath = os.path.abspath(
      os.path.expanduser(socketPath)
    )

  def connect(self) :
    """Connect to the Unix domain socket specified in __init__."""
    if socket.AF_UNIX is None :
      print("ERROR: currently you can only use this tool on Unix derivatives")
      sys.exit(-1)

    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    self.sock.connect(self.socketPath)
