# This file contains commands to setup the MajorDomo.

import asyncio
import click
import os
import platform
import yaml

from cpcli.utils import getDataFromMajorDomo, postDataToMajorDomo
from cpcli.commands.projects import add

@click.command(
  short_help="Setup your MajorDomo.",
  help="Setup your MajorDomo."
)
@click.pass_context
def setup(ctx) :
  """Setup your MajorDomo."""

  config = ctx.obj
  config = config['config']

  if 'setup' not in config : config['setup'] = {}
  setup = config['setup']

  if 'projects' not in setup : setup['projects'] = {}
  projects = setup['projects']

  for aProjDir in projects :
    print("\nAdding projects in {}".format(aProjDir))
    ctx.invoke(add, projectnames=None, projectdir=aProjDir)
