# This is the base of the extensible ComputePods command line interface
# system.

import click
import sys
import yaml

from cpcli.utils import loadConfiguration, importCommands

config = loadConfiguration()

@click.group()
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
