# This is the base of the extensible ComputePods command line interface
# system.

import click
import sys
import yaml

from cpcli.utils import loadConfiguration, importCommands

config = loadConfiguration()

@click.group()
def cli() :
  pass

importCommands(config, cli)

