# This file contains the projects command which interacts with the
# MajorDomo's projects interface.

import asyncio
import click
import os
import platform
import yaml

import cputils.yamlLoader
from cpcli.utils import runCommandWithNatsServer, \
  getDataFromMajorDomo, postDataToMajorDomo

def fixUpProjDir(configData, yamlPath, newYamlData) :
  if 'projects' not in newYamlData : return
  for projName, projDesc in newYamlData['projects'].items() :
    if 'targets' not in projDesc : continue
    targets = projDesc['targets']
    if 'defaults' not in targets: targets['defaults'] = {}
    defaults = targets['defaults']
    if 'projectDir' not in defaults :
      defaults['projectDir'] = str(yamlPath.parent)

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
@click.option('-p', '--projectNames', multiple=True,
  help="one or more project names to be added (default: add all found)"
)
@click.option('-d', '--projectDir', default=os.getcwd(),
  help="a directory containing a project description yaml file (.pyaml)"
)
@click.pass_context
def add(ctx, projectnames, projectdir) :

  if not os.path.isdir(projectdir) :
    print("Project directory not found:\n  {}".format(projectdir))
    return

  projects = {}
  cputils.yamlLoader.loadYamlFrom(
    projects, projectdir, [ '.PYML'], fixUpProjDir
  )

  projectsFound = False
  if 'projects' in projects :
    for aProjectName, aProjectDesc in projects['projects'].items() :
      if projectnames and aProjectName not in projectnames : continue
      projectsFound = True
      result = postDataToMajorDomo('/project/add', {
        'rsyncHost'   : platform.node(),
        'rsyncUser'   : os.getlogin(),
        'projectName' : aProjectName,
        'projectDir'  : projectdir,
        'projectDesc' : aProjectDesc
      })

      print("---------------------------------------------------------")
      print(yaml.dump(result))
      print("---------------------------------------------------------")
  if not projectsFound :
    print("No projects found in the directory.")
    if projectnames : print("  Projects:  [{}]".format(projectnames))
    print("  Directory: {}".format(projectdir))

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
    projects, aProjectDir, [ '.PYML'], fixUpProjDir
  )

  projectsFound = False
  if 'projects' in projects :
    for aProjectName, aProjectDesc in projects['projects'].items() :
      if projectname and aProjectName not in projectname : continue
      projectsFound = True
      result = postDataToMajorDomo('/project/update', {
        'rsyncHost'   : platform.node(),
        'rsyncUser'   : os.getlogin(),
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
    projects, aProjectDir, [ '.PYML'], fixUpProjDir
  )

  projectsFound = False
  if 'projects' in projects :
    for aProjectName, aProjectDesc in projects['projects'].items() :
      if projectname and aProjectName not in projectname : continue
      projectsFound = True
      result = postDataToMajorDomo('/project/remove', {
        'rsyncHost'   : platform.node(),
        'rsyncUser'   : os.getlogin(),
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
    short_help="list targets for an existing project.",
    help="List targets for an existing project"
)
@click.argument('projectName')
@click.pass_context
def targets(ctx, projectname) :
  print("Listing targets...")
  data = getDataFromMajorDomo(f'/project/targets/{projectname}')
  print("")
  print(yaml.dump(data))
  print("")

@projects.command(
    short_help="return the definition for an existing project.",
    help="Return the definition for an existing project"
)
@click.argument('projectName')
@click.pass_context
def definition(ctx, projectname) :
  print("Project definition...")
  data = getDataFromMajorDomo(f'/project/definition/{projectname}')
  print("")
  print(yaml.dump(data))
  print("")

@projects.command(
    short_help="build definition for the target of an existing project.",
    help="Build definition for the target of an existing project"
)
@click.argument('projectName')
@click.argument('target')
@click.pass_context
def build(ctx, projectname, target) :
  print(f"Target build definition... ({projectname}, {target})")
  data = getDataFromMajorDomo(f'/project/buildTarget/{projectname}/{target}')
  print("")
  print(yaml.dump(data))
  print("")

async def echoNatsMessages(aSubject, theSubject, theMsg) :
  if isinstance(theMsg, str) and theMsg[1] != 'D' :
    print(theMsg.strip("\""))
  elif isinstance(theMsg, dict) :
    if 'retCode' in theMsg :
      print(f"completed with code: {theMsg['retCode']}")
      print("\n--------------------------------------------------------------------------------\n")

async def monitorBuild(data, config, natsClient) :
  projectName = data['projectName']
  target      = data['target']

  await natsClient.listenToSubject(
    f"logger.{projectName}.{target}", echoNatsMessages
  )
  await natsClient.listenToSubject(
    f"*.build.from.*.{projectName}.{target}", echoNatsMessages
  )

  waitIndefinitely = asyncio.Event()
  await waitIndefinitely.wait()

@projects.command(
    short_help="monitor the build of a target of an existing project.",
    help="Monitor the build of a target of an existing project"
)
@click.argument('projectName')
@click.argument('target')
@click.pass_context
def monitor(ctx, projectname, target) :
  print(f"Monitoriing the building of... ({projectname}, {target})")
  runCommandWithNatsServer(
    { 'projectName' : projectname, 'target' : target},
    monitorBuild
  )
  print("Done!")
