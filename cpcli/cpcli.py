# This is the base of the extensible ComputePods command line interface
# system.

import click
import sys
import yaml

#######################################################################
# start by monkey patching click to allow aliased commands
# adapted from:
#   https://click.palletsprojects.com/en/8.1.x/advanced/#command-aliases
#
def aliased_get_command(self, ctx, cmd_name) :
  possibleCmd = self.orig_get_command(ctx, cmd_name)
  if possibleCmd is not None:
    return possibleCmd
  matches = [aCmd for aCmd in self.list_commands(ctx)
             if aCmd.startswith(cmd_name)]
  if not matches:
    return None
  elif len(matches) == 1:
    return self.orig_get_command(ctx, matches[0])
  ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

def aliased_resolve_command(self, ctx, args):
  # always return the full command name
  _, cmd, args = self.orig_resolve_command(ctx, args)
  return cmd.name, cmd, args

click.Group.orig_get_command = click.Group.get_command
click.Group.get_command = aliased_get_command

click.Group.orig_resolve_command = click.Group.resolve_command
click.Group.resolve_command = aliased_resolve_command

#######################################################################

from cpcli.utils import loadConfiguration, importCommands

config = loadConfiguration()

contextSettings = dict(
   obj={
     'config' : config
   }
)

@click.group(context_settings=contextSettings)
@click.option('-c', '--config',
  help="path to an additional configuration file [default: ./cpcli.conf]"
)
@click.option('-t', '--tester', is_flag=True,
  help="run tests by ignoring the standard commands [default: no testing]"
)
@click.option('-v', '--verbose', count=True,
  help="increase the verbosity [default: 0]"
)
def cli(verbose, tester, config) :
  pass

importCommands(cli)
