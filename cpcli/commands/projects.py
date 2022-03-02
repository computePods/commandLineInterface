# This file contains the projects command which interacts with the
# MajorDomo's projects interface.

import click
import os
import yaml

from cpcli.utils import getDataFromMajorDomo, postDataToMajorDomo

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
  data = getDataFromMajorDomo('/projects')
  print("")
  print(yaml.dump(data))
  print("")

@projects.command(
    short_help="add a project.",
    help="Add a project"
)
@click.argument("projectName")
@click.pass_context
def add(ctx, projectname) :
  projectName = projectname
  projectDir = os.getcwd()
  print("adding project [{}]".format(projectName))
  print("projectDir [{}]".format(projectDir))
  postDataToMajorDomo('/project/add', {
    'projectName' : projectName,
    'projectDir'  : projectDir
  })

@projects.command(
    short_help="remove a project.",
    help="Remove a project"
)
@click.argument("projectName")
@click.pass_context
def remove(ctx, projectname) :
  projectName = projectname
  projectDir  = os.getcwd()
  print("removing project [{}]".format(projectName))
  print("projectDir [{}]".format(projectDir))
  postDataToMajorDomo('/project/remove', {
    'projectName' : projectName,
    'projectDir'  : projectDir
  })
