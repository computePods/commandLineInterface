# This file contains commands to manager the rsync and ssh keys.

import asyncio
import click
import os
import platform
import yaml

from cputils.rsyncFileTransporter import RsyncFileTransporter
from cpcli.utils import getDataFromMajorDomo, postDataToMajorDomo

@click.group(
  short_help="Rsync files and manage ssh keys and agents.",
  help="Rsync files to/from a ComputePod Chef as well as manage the associated ssh keys and agents."
)
def ssh() :
  """Click group command used to collect all of the rsync/ssh commands."""

  pass

def registerCommands(theCli) :
  """Register the ssh command with the main cli click group command."""

  theCli.add_command(ssh)

# This next command enables (adds) the ssh key for this ComputePod to the
# user's authorized_keys file.

async def asyncEnableKey(config) :
  rsync = RsyncFileTransporter(config)
  rsyncPublicKey = getDataFromMajorDomo('/security/rsyncPublicKey')
  if rsyncPublicKey == "unknown" :
    print("No public key obtained from MajorDomo")
  else :
    if await rsync.enableKey(publicKey=rsyncPublicKey) :
      print("Ssh key for this ComputePod has been added to your ssh authorized_keys file")
    else :
      print("Could not add the ssh key for this ComputePod to your ssh authorized_keys file")

  if 'hostPublicKeyFile' in config['config'] :
    hostPublicKeyFile = os.path.abspath(os.path.expanduser(
      config['config']['hostPublicKeyFile']
    ))
    hostPublicKey = None
    if os.path.exists(hostPublicKeyFile) \
      and os.access(hostPublicKeyFile, os.R_OK) :
      with open(hostPublicKeyFile, 'r') as hpkf :
        hostPublicKey = hpkf.read().strip()
    result = "Could not read"
    if hostPublicKey :
      result = postDataToMajorDomo('/security/addHostPublicKey', {
        'host'      : platform.node(),
        'publicKey' : hostPublicKey
      })
      if result is None :
        result = "Could not contact majorDomo with"
      else :
        result = result['result']
    print(f"{result} this host's public key")
  else :
    print("\nWARNING: Could not determine this host's public key")
    print("Please specify the location of the ssh host public key")
    print("in the configuration file.")

@ssh.command(
  short_help="Enable the ssh key for this ComputePod for this user.",
  help="Enable the ssh key for this ComputePod for this user.")
@click.option('-C', '--consult', is_flag=True, default=False,
    help=f"whether or not to consult the local MajorDomo [default: False]"
)
@click.option('-r', '--restricteddir',
  help="a directory into/from which all rsync is restricted [no default]"
)
@click.option('-a', '--alloweddir', multiple=True,
    help="an additional allowed directory"
)
@click.option('-l', '--logdir',
    help="adds the specified log file directory as an allowed directory"
)
@click.pass_context
def enable(ctx, consult, restricteddir, alloweddir, logdir) :
  alloweddir = list(alloweddir)

  config = ctx.obj
  if 'ssh' not in config['config'] :
    config['config']['ssh'] = { }
  sshConfig = config['config']['ssh']
  if consult :
    config['ssh']['cprsyncConsult']       = consult
  if restricteddir :
    config['ssh']['cprsyncRestrictedDir'] = restricteddir
  if logdir :
    alloweddir.append(logdir)
  if alloweddir :
    config['ssh']['cprsyncAllowedDirs']   = alloweddir
  asyncio.run(asyncEnableKey(config))

# This next command disables (removes) the ssh key for this ComputePod
# from the user's authorized_keys file.

async def asyncDisableKey(config) :
  rsync = RsyncFileTransporter(config)

  if await rsync.disableKey() :
    print("Ssh key for this ComputePod has been removed from your ssh authorized_keys file")
  else :
    print("Could not remove the ssh key for this ComputePod from your ssh authorized_keys file")
  result = postDataToMajorDomo('/security/removeHostPublicKey', {
    'host' : platform.node()
  })
  if result is None :
    result = "Could not contact majorDomo with"
  else :
    result = result['result']
  print(f"{result} this host's public key")

@ssh.command(
  short_help="Disable the ssh key for this ComputePod for this user.",
  help="Disable the ssh key for this ComputePod for this user.")
@click.pass_context
def disable(ctx) :
  config = ctx.obj
  asyncio.run(asyncDisableKey(config))
