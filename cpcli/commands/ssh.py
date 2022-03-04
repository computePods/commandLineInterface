# This file contains commands to manager the rsync and ssh keys.

import asyncio
import click
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

## This next command creates the ssh key required for this user to send
## files to/from ComputePods chefs using rsync.
#
#async def asyncCreateSshKey(config) :
#  rsync = RsyncFileTransporter(config)
#  if await rsync.keyExists() :
#    print("Existing ssh/rsync key found.")
#  else :
#    if await rsync.createdKey() :
#      print("New ssh/rsync key created")
#    else :
#      print("FAILED to create a new ssh/rsync key")
#
#@ssh.command(
#  short_help="Create a new ssh key for use with rsync in this ComputePod.",
#  help="Create a new ssh key for use with rsync in this ComputePod.")
#@click.pass_context
#def create(ctx) :
#  config = ctx.obj
#  asyncio.run(asyncCreateSshKey(config))

# This next command starts the ssh-agent required for this user to send
# files to/from ComputePods chefs using rsync.
#
#async def asyncStartSshAgent(config) :
#  rsync = RsyncFileTransporter(config)
#  if await rsync.startedAgent() :
#    print("ComputePods rsync transporter ssh-agent started")
#  else :
#    print("FAILED to start the ComputePods rsync transporter ssh-agent")
#
#@ssh.command(
#  short_help="Start an ssh-agent for use with this ComputePod.",
#  help="Start an ssh-agent for use with this ComputePod.")
#@click.pass_context
#def start(ctx) :
#  config = ctx.obj
#  asyncio.run(asyncStartSshAgent(config))

# This next command stops the ssh-agent required for this user to send
# files to/from ComputePods chefs using rsync.
#
#async def asyncStopSshAgent(config) :
#  rsync = RsyncFileTransporter(config)
#  await rsync.stopAgent()
#  print("Stopped ssh-agent for this ComputePod")
#
#@ssh.command(
#  short_help="Stop the ssh-agent used by this ComputePod.",
#  help="Stop the ssh-agent used by this ComputePod.")
#@click.pass_context
#def stop(ctx) :
#  config = ctx.obj
#  asyncio.run(asyncStopSshAgent(config))

# This next command loads an ssh key into the running ssh-agent required
# for this user to send files to/from ComputePods chefs using rsync.
#
#async def asyncLoadedKey(config) :
#  rsync = RsyncFileTransporter(config)
#  if not await rsync.isSshAgentRunning() :
#    if not await rsync.startedAgent() :
#      print("Could not start the ssh-agent for this ComputePod")
#      return
#
#  if await rsync.loadedKey() :
#    print("Ssh key loaded into the ssh-agent for this ComputePod")
#  else :
#    print("FAILED to load the ssh key into the ssh-agent for this ComputePod")
#
#@ssh.command(
#  short_help="Load the ssh key into the ssh-agent for this ComputePod.",
#  help="Load the ssh key into the ssh-agent for this ComputePod.")
#@click.pass_context
#def load(ctx) :
#  config = ctx.obj
#  asyncio.run(asyncLoadedKey(config))

# This next command unloads an ssh key from the running ssh-agent required
# for this user to send files to/from ComputePods chefs using rsync.
#
#async def asyncUnLoadedKey(config) :
#  rsync = RsyncFileTransporter(config)
#  if not await rsync.isSshAgentRunning() :
#    if not await rsync.startedAgent() :
#      print("Could not start the ssh-agent for this ComputePod")
#      return
#
#  if await rsync.unloadedKey() :
#    print("Ssh key unloaded from the ssh-agent for this ComputePod")
#  else :
#    print("FAILED to unload the ssh key from the ssh-agent for this ComputePod")
#
#@ssh.command(
#  short_help="Unload the ssh key from the ssh-agent for this ComputePod.",
#  help="Unload the ssh key from the ssh-agent for this ComputePod.")
#@click.pass_context
#def unload(ctx) :
#  config = ctx.obj
#  asyncio.run(asyncUnLoadedKey(config))

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

@ssh.command(
  short_help="Enable the ssh key for this ComputePod for this user.",
  help="Enable the ssh key for this ComputePod for this user.")
@click.option('-d', '--dir',
  help="Specify the base directory inside which rsync is allowed."
)
@click.pass_context
def enable(ctx, dir) :
  config = ctx.obj
  if dir :
    if 'ssh' not in config :
      config['ssh'] = { }
    config['ssh']['cprsyncCtlDir'] = dir
  asyncio.run(asyncEnableKey(config))

# This next command disables (removes) the ssh key for this ComputePod
# from the user's authorized_keys file.

async def asyncDisableKey(config) :
  rsync = RsyncFileTransporter(config)

  if await rsync.disableKey() :
    print("Ssh key for this ComputePod has been removed from your ssh authorized_keys file")
  else :
    print("Could not remove the ssh key for this ComputePod from your ssh authorized_keys file")

@ssh.command(
  short_help="Disable the ssh key for this ComputePod for this user.",
  help="Disable the ssh key for this ComputePod for this user.")
@click.pass_context
def disable(ctx) :
  config = ctx.obj
  asyncio.run(asyncDisableKey(config))

# This next command rsyncs files from the fromPath to the toPath using
# this ComputePod's ssh key.
#
#async def asyncRsyncedFiles(config, fromPath, toPath) :
#  rsync = RsyncFileTransporter(config)
#
#  success, stdout, stderr = await rsync.rsyncedFiles(fromPath, toPath)
#  if success :
#    print(f"Rsynced files from {fromPath} to {toPath}")
#  else :
#    print(f"Could not rsync files from {fromPath} to {toPath}")
#
#@ssh.command(
#  short_help="Rsync files from fromPath to toPath using the ssh key for this ComputePod.",
#  help="Rsync files from fromPath to toPath using the ssh key for this ComputePod."
#)
#@click.argument("fromPath")
#@click.argument("toPath")
#@click.pass_context
#def rsync(ctx, frompath, topath) :
#  config = ctx.obj
#  asyncio.run(asyncRsyncedFiles(config, frompath, topath))
