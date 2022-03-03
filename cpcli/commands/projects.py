# This file contains the projects command which interacts with the
# MajorDomo's projects interface.

import click
import os
import yaml

import cputils.yamlLoader
from cpcli.utils import getDataFromMajorDomo, postDataToMajorDomo

@click.group(
  short_help="Manage MajorDomo projects.",
  help="Manage MajorDomo projects."
)
def projects() :
  """Click group command used to collect all of the project commands."""

  pass

def registerCommands(theCli) :
  """Register the projects command with the main cli click group command."""

  theCli.add_command(projects)


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
@click.option('-p', '--projectName', multiple=True,
  help="a project name to be added (default: add all found)"
)
@click.pass_context
def add(ctx, projectname) :
  aProjectDir = os.getcwd()

  projects = {}
  cputils.yamlLoader.loadYamlFrom(
    projects, aProjectDir, [ '.PYML'],
  )

  projectsFound = False
  if 'projects' in projects :
    for aProjectName, aProjectDesc in projects['projects'].items() :
      if projectname and aProjectName not in projectname : continue
      projectsFound = True
      result = postDataToMajorDomo('/project/add', {
        'projectName' : aProjectName,
        'projectDir'  : aProjectDir,
        'projectDesc' : aProjectDesc
      })

      print("---------------------------------------------------------")
      print(yaml.dump(result))
      print("---------------------------------------------------------")
  if not projectsFound :
    print("None of the listed projects have descriptions in this directory.")

@projects.command(
    short_help="update an existing project.",
    help="Update an exiting a project"
)
@click.option('-p', '--projectName', multiple=True,
  help="a project name to be updated (default: update all found)"
)
@click.pass_context
def update(ctx, projectname) :
  aProjectDir = os.getcwd()

  projects = {}
  cputils.yamlLoader.loadYamlFrom(
    projects, aProjectDir, [ '.PYML'],
  )

  projectsFound = False
  if 'projects' in projects :
    for aProjectName, aProjectDesc in projects['projects'].items() :
      if projectname and aProjectName not in projectname : continue
      projectsFound = True
      result = postDataToMajorDomo('/project/update', {
        'projectName' : aProjectName,
        'projectDir'  : aProjectDir,
        'projectDesc' : aProjectDesc
      })

      print("---------------------------------------------------------")
      print(yaml.dump(result))
      print("---------------------------------------------------------")
  if not projectsFound :
    print("None of the listed projects have descriptions in this directory.")

@projects.command(
    short_help="remove an existing project.",
    help="Remove an existing project"
)
@click.option('-p', '--projectName', multiple=True,
  help="a project name to be updated (default: update all found)"
)
@click.pass_context
def remove(ctx, projectname) :
  aProjectDir  = os.getcwd()

  projects = {}
  cputils.yamlLoader.loadYamlFrom(
    projects, aProjectDir, [ '.PYML'],
  )

  projectsFound = False
  if 'projects' in projects :
    for aProjectName, aProjectDesc in projects['projects'].items() :
      if projectname and aProjectName not in projectname : continue
      projectsFound = True
      result = postDataToMajorDomo('/project/remove', {
        'projectName' : aProjectName,
        'projectDir'  : aProjectDir,
        'projectDesc' : aProjectDesc
      })

      print("---------------------------------------------------------")
      print(yaml.dump(result))
      print("---------------------------------------------------------")
  if not projectsFound :
    print("None of the listed projects have descriptions in this directory.")
