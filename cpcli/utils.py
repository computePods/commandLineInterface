""" A collection of utilities for cpcli."""

import click
import inspect
import importlib
import json
import os
import pkgutil
import sys
import yaml

from cpcli.httpUnixDomainClient import HTTPUnixDomainConnection

defaultConfig = {
  'socketPath'  : '~/.local/cpmd/server.socket',
  'commandsDir' : [ 'commands' ]
}

config = { }

def loadConfiguration() :
  """Prescan the command line arguments for configuration and verbose
  switches. Load any specified yaml configuration files and turn on
  verbose mode if requested. We do this *before* the click argument
  processing takes over."""

  global config

  verbosity = 0
  while True :
    verboseIndex = -1
    if '-v' in sys.argv        : verboseIndex = sys.argv.index('-v')
    if '--verbose' in sys.argv : verboseIndex = sys.argv.index('--verbose')

    if -1 < verboseIndex :
      del sys.argv[verboseIndex:verboseIndex+1]
      verbosity = verbosity + 1
    else :
      break

  configIndex = -1
  if '-c' in sys.argv       : configIndex = sys.argv.index('-c')
  if '--config' in sys.argv : configIndex = sys.argv.index('--config')
  configPath = './cpcli.conf'
  if -1 < configIndex :
    del sys.argv[configIndex:configIndex+1]
    configPath = sys.argv[configIndex:configIndex+1][0]
    del sys.argv[configIndex:configIndex+1]
  config = defaultConfig
  try :
    with open(configPath) as configFile :
      config = yaml.safe_load(configFile.read())
    if 0 < verbosity : print(f"Loaded configuration from [{configPath}]")
  except FileNotFoundError :
    if 0 < verbosity : print(f"Could not load configuration from [{configPath}]")
  except Exception as err :
    print(f"Could not load configuration from [{configPath}]")
    print(repr(err))
  config['socketPath'] = os.path.abspath(
    os.path.expanduser(config['socketPath'])
  )
  config['verbosity']  = verbosity
  if 0 < verbosity :
    print("--------------------------------------------------------------")
    print(yaml.dump(config))
    print("--------------------------------------------------------------")
  return config

def loadPythonCommandsIn(aCommandDir, aPkgPath, theCli) :
  """Load/import all python based click commands found in the aCommandDir
  directory. """

  for (_, module_name, _) in pkgutil.iter_modules([aCommandDir]) :
    theModule = importlib.import_module(aPkgPath+'.'+module_name)
    for (aName, anObj) in inspect.getmembers(theModule) :
      if isinstance(anObj, click.Command) :
        if 0 < config['verbosity'] :
          print(f"adding click command [{aName}] from [{aPkgPath}.{module_name}]")
        theCli.add_command(anObj)


def loadYamlCommandsIn(aCommandDir, theCli) :
  """Load all yaml based click command files found in the aCommandDir
  directory. """

  for aFile in os.listdir(aCommandDir) :
    if aFile.endswith('.yaml') :
      try :
        with open(os.path.join(aCommandDir, aFile)) as yamlCmdFile :
          yamlCmd = yaml.safe_load(yamlCmdFile.read())
          if not isinstance(yamlCmd, dict) : yamlCmd = {}
      except Exception as err :
        print(repr(err))
        yamlCmd = { }

      if ('longHelp' in yamlCmd) and ('shortHelp' in yamlCmd) :
        if 0 < config['verbosity'] :
          print(f"adding click command [{aFile}] in [{aCommandDir}]")
        if 'name' not in yamlCmd : yamlCmd['name'] = aFile.replace('.yaml', '')
        epilogHelp = ""
        if 'epilogHelp' in yamlCmd : epilogHelp = yamlCmd['epilogHelp']
        @theCli.command(
          yamlCmd['name'],
          help=yamlCmd['longHelp'],
          short_help=yamlCmd['shortHelp'],
          epilog=epilogHelp
        )
        def yamlCallback(*args, **kwargs) :
          print(f"Running {yamlCmd['name']}...")
          print("--------------------------------------------------------")
          print(yaml.dump(args))
          print("--------------------------------------------------------")
          print(yaml.dump(kwargs))
          print("--------------------------------------------------------")
          print(yaml.dump(yamlCmd))
          print("--------------------------------------------------------")

def importCommands(cli) :
  """Import or load all python or yaml based click commands found in any
  of the commandDirs directories."""

  commandDirs = []
  if 'commandDirs' in config : commandDirs = config['commandDirs']
  commandDirs.insert(0, 'cpcli/commands')
  for aCommandDir in commandDirs :
    pkgPath = aCommandDir.replace('/','.')
    if aCommandDir.startswith('cpcli') :
      aCommandDir = os.path.join(os.path.dirname(__file__), aCommandDir.replace('cpcli/', ''))
    if not aCommandDir.startswith('/') :
      currentWD = os.path.abspath(os.getcwd())
      if currentWD not in sys.path :
        sys.path.insert(0, currentWD)
    loadPythonCommandsIn(aCommandDir, pkgPath, cli)
    loadYamlCommandsIn(aCommandDir, cli)

def getDataFromMajorDomo(method, url) :
  result = None
  try :
    http = HTTPUnixDomainConnection(config['socketPath'])
    http.request(method, url)
    result = json.loads(http.getresponse().read())
  except Exception as err :
    sys.stderr.write("\nERROR: Could not connect to a MajorDomo at [{}]\n".format(config['socketPath']))
    sys.stderr.write("  {}\n".format(repr(err)))

  return result