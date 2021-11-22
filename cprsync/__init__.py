# This is the ComputePods rsync controller (a command line interface to
# the MajorDomo's projects interface).

# We ONLY use standard Python libraries

import argparse
import datetime
from http.client import HTTPConnection
import json
import os
import socket
import sys

# The one MOST important default
#   the path to the user's MajorDomo server
#
defaultSocketPath = '~/.local/cpmd/server.socket'
defaultLogPath    = '/tmp/cprsync.log'

# Turn off tracebacks so that we DO NOT tell any end user about this code
#
sys.tracebacklimit = 0

# We need to subclass the standard HttpConnection to allow the use of unix
# domain sockets
#
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

# Now we do the main task
#
def ctl() :

  # Setup the command line argument parser
  #
  parser = argparse.ArgumentParser(
    description="Control rsync connections from ComputePod chefs."
  )
  parser.add_argument("-s", "--socket", type=str,
    help=f"a path to the user's MajorDomo server [default: {defaultSocketPath}]"
  )
  parser.add_argument("-l", "--log", type=str,
    help=f"a path to the cprsync's log file [default: {defaultLogPath}]"
  )
  parser.add_argument("-d", "--dir", type=str,
    help="a path to the base directory into/from which rsync is allowed [no default]"
  )
  args = parser.parse_args()

  # normalise the command line arguments
  #
  socketPath = defaultSocketPath
  if args.socket :
    socketPath = args.socket
  socketPath = os.path.abspath(os.path.expanduser(socketPath))
  logFilePath = defaultLogPath
  if args.log :
    logFilePath = args.log
  logFilePath = os.path.abspath(os.path.expanduser(logFilePath))

  # Get the original command
  #
  origCmd = os.getenv("SSH_ORIGINAL_COMMAND", "")
  cmdParts = origCmd.split()

  # Exit if this is NOT an rsync command of the correct length
  #
  if len(cmdParts) < 5 or cmdParts[0].find('rsync') < 0 :
    sys.stderr.write("You can ONLY use rsync using this ssh key!\n")
    sys.exit(-1)

  # Normalise the rsync command
  #
  targetDir = cmdParts.pop()
  if not targetDir.startswith('/') :
    targetDir = os.path.abspath(os.path.expanduser('~/'+targetDir))
  cmdParts.append(targetDir)
  cmdParts[0] = '/usr/bin/rsync'

  # Get the allowed project paths from this user's MajorDomo
  #
  projects = { }
  if args.dir :
    majorDomoOK = args.dir
    projects['allowedDir'] = os.path.abspath(
      os.path.expanduser(args.dir)
    )
  else :
    majorDomoOK = socketPath
    try :
      http = HTTPUnixDomainConnection(socketPath)
      http.request('GET', '/projects')
      result = http.getresponse()
      projects = json.loads(result.read())
    except Exception as err :
      majorDomoOK = repr(err)

  # Check if this targetDir is an allowed project path
  #
  rsyncOK = False
  for anOkPath in projects.values() :
    if targetDir.startswith(anOkPath) :
      rsyncOK = True
      break

  # Log this result
  #
  with open(logFilePath, 'a') as logFile :
    logFile.write("---------------------------------------------------------\n")
    logFile.write("time now: [{}]\n\n".format(datetime.datetime.now()))
    logFile.write("original ssh command: \n  [{}]\n\n".format(origCmd))
    logFile.write("new command: \n")
    for aCmdPart in cmdParts :
      logFile.write(f"  - {aCmdPart}\n")
    logFile.write("\n")
    logFile.write("majorDomoOK: {}\n".format(majorDomoOK))
    logFile.write("rsyncOK:     {}\n".format(rsyncOK))
    logFile.write("\nallowed projects:\n")
    for aProjectName, aProjectPath in projects.items() :
      logFile.write(f"  {aProjectName}: {aProjectPath}\n")
    logFile.write("\n")

  # Now do the rsync IF we are allowed
  #
  if rsyncOK : os.execv('/usr/bin/rsync', cmdParts)
  else : sys.stderr.write("Access DENIED!\n")
