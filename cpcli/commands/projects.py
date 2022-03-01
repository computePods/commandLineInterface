# This file contains the projects command which interacts with the
# MajorDomo's projects interface.

import click
import yaml

from cpcli.utils import getDataFromMajorDomo

@click.group(
  short_help="Manage MajorDomo projects.",
  help="Manage MajorDomo projects."
)
def projects() :
  """Click group command used to collect all of the project commands."""

  pass

def registerCommands(theClie) :
  """Register the projects command with the main cli click group command."""

  theClie.add_command(projects)



@projects.command(
  short_help="list projects",
  help="List all projects known to the local MajorDomo."
)
@click.pass_context
def list(ctx) :
  print("Listing projects...")
  data = getDataFromMajorDomo('GET', '/projects')
  print("")
  print(yaml.dump(data))
  print("")

#@projects.command(
#    short_help="add a project.",
#    help="Add a project"
#)
#@click.argument("projectDir")
#@click.pass_context
#def add(ctx, projectdir) :
#  print("adding {}".format(projectdir))

#@projects.command(
#    short_help="remove a project.",
#    help="Remove a project"
#)
#@click.argument("projectDir")
#@click.pass_context
#def remove(ctx, projectdir) :
#  print("remove {}".format(projectdir))
