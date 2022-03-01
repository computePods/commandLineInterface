""" A collection of utilities for cpcli."""

import asyncio
import click
from deepdiff import DeepDiff
import inspect
import importlib
import json
import os
import pkgutil
from pprint import pprint
import sys
import yaml

from cputils.natsClient import NatsClient
from cpcli.httpUnixDomainClient import HTTPUnixDomainConnection

defaultConfig = {
  'socketPath'  : '~/.local/cpmd/server.socket',
  'commandsDirs' : [ ]
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

  testerIndex = -1
  if '-t'      in sys.argv : testerIndex = sys.argv.index('-t')
  if '-tester' in sys.argv : testerIndex = sys.argv.index('-tester')
  if -1 < testerIndex :
    del sys.argv[testerIndex:testerIndex+1]

  configIndex = -1
  if '-c'       in sys.argv : configIndex = sys.argv.index('-c')
  if '--config' in sys.argv : configIndex = sys.argv.index('--config')
  configPath = './cpcliConfig.yaml'
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

  if 'socketPath' not in config :
    config['socketPath'] = defaultConfig['socketPath']
  config['socketPath'] = os.path.abspath(
    os.path.expanduser(config['socketPath'])
  )

  if 'commandsDirs' not in config :
    config['commandsDirs'] = defaultConfig['commandsDirs']
  if testerIndex < 0 :
    config['commandsDirs'].insert(0,'cpcli/commands')

  config['verbosity']  = verbosity

  # if we are in tester mode... look for a test command...
  # if there is not test command ... add the runAllTests command ...
  #
  if -1 < testerIndex :
    config['testerMode'] = True
    numArguments = 0
    for anArg in sys.argv :
      if not anArg.startswith('-') :
        numArguments = numArguments + 1
    if numArguments < 2 :
      sys.argv.append('runAllTests')

  if 0 < verbosity :
    print("--------------------------------------------------------------")
    print(yaml.dump(config))
    print("--------------------------------------------------------------")
  return config

loadedTests = { }

def loadPythonCommandsIn(aCommandDir, aPkgPath, theCli) :
  """Load/import all python based click commands found in the aCommandDir
  directory. """

  for (_, module_name, _) in pkgutil.iter_modules([aCommandDir]) :
    theModule = importlib.import_module(aPkgPath+'.'+module_name)
    if hasattr(theModule, 'registerCommands') :
      theModule.registerCommands(theCli)
    else :
      for (aName, anObj) in inspect.getmembers(theModule) :
        if hasattr(anObj, 'cpTest') :
          if 0 < config['verbosity'] :
            print(f"adding test [{aName}] from {aCommandDir}")
          loadedTests[aName] = anObj
          continue
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

      if 'testName' in yamlCmd :
        if 0 < config['verbosity'] :
          print("adding test: [{}] from [{}]".format(
            yamlCmd['testName'], aCommandDir
          ))
        loadedTests[yamlCmd['testName']] = yamlCmd
        continue

      if ('longHelp' in yamlCmd) and ('shortHelp' in yamlCmd) :
        if 0 < config['verbosity'] :
          print(f"adding click command [{aFile}] in [{aCommandDir}]")
        if 'name' not in yamlCmd : yamlCmd['name'] = aFile.replace('.yaml', '')
        if 'epilogHelp' not in yamlCmd : yamlCmd['epilogHelp'] = ""
        @theCli.command(
          yamlCmd['name'],
          help=yamlCmd['longHelp'],
          short_help=yamlCmd['shortHelp'],
          epilog=yamlCmd['epilogHelp']
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

def runCommandWithNatsServer(commandMethod) :
  if callable(commandMethod)                      :
    if asyncio.iscoroutinefunction(commandMethod) :
      async def runCommand() :
        natsClient = NatsClient("majorDomo", 10)
        host = "127.0.0.1"
        port = 4222
        if 'natsServer' in config :
          natsServerConfig = config['natsServer']
          if 'host' in natsServerConfig : host = natsServerConfig['host']
          if 'port' in natsServerConfig : port = natsServerConfig['port']
        natsServerUrl = f"nats://{host}:{port}"
        print(f"connecting to nats server: [{natsServerUrl}]")
        await natsClient.connectToServers([ natsServerUrl ])
        try:
          await commandMethod(config, natsClient)
        finally:
          await natsClient.closeConnection()
      asyncio.run(runCommand())
    else : print("command MUST be an asyncio coroutine")
  else : print("command MUST be an asyncio coroutine")

def runYamlTest(yamlTest) :
  if 'request' not in yamlTest :
    print("No request found in {}.... nothing to do!".format(
      yamlTest['testName']))
    return
  request = yamlTest['request']
  if request is not None and (
    'method' not in request or 'url' not in request) :
    print("No method or url specified in request for {}... nothing to do!".format(
      yamlTest['testName']
    ))
    return
  result = getDataFromMajorDomo(request['method'], request['url'])

  if 'expected' in yamlTest :
    diff   = DeepDiff(result, yamlTest['expected'])
    print("---------------------------------------------------------------")
    pprint(diff, indent=2)
    print("---------------------------------------------------------------")

def runASingleTest(testName, testMethod) :
  print("\n==========================================================")
  print(f"running test: {testName}")
  if callable(testMethod)                      :
    if asyncio.iscoroutinefunction(testMethod) :
      async def runATest() :
        print("RUNNING A TEST")
        natsClient = NatsClient("majorDomo", 10)
        host = "127.0.0.1"
        port = 4222
        if 'natsServer' in config :
          natsServerConfig = config['natsServer']
          if 'host' in natsServerConfig : host = natsServerConfig['host']
          if 'port' in natsServerConfig : port = natsServerConfig['port']
        natsServerUrl = f"nats://{host}:{port}"
        print(f"connecting to nats server: [{natsServerUrl}]")
        await natsClient.connectToServers([ natsServerUrl ])
        try:
          await testMethod(config, natsClient)
        finally:
          await natsClient.closeConnection()
        print("RAN A TEST")
      asyncio.run(runATest())
    else                                  : testMethod(config)
  else                                    : runYamlTest(testMethod)

def addRunAllTests(theCli) :
  if 'testerMode' in config :
    if 0 < config['verbosity'] :
      print("Adding runAllTests command")
    @theCli.command('runAllTests',
      help="Run all known tests",
      short_help="Run all known tests"
    )
    def runAllTestsCallback(*args, **kwargs) :
      sys.argv.remove('runAllTests')
      for aTestName, aTest in loadedTests.items() :
        runASingleTest(aTestName, aTest)

def addRunTest(theCli) :
  if 'testerMode' in config :
    if 0 < config['verbosity'] :
      print("Adding runTest command to run one test")
    @theCli.command('runTest',
      help="Run a single test",
      short_help="Run a single test"
    )
    @click.argument('testName')
    def runTestCallback(testname) :
      if testname in loadedTests :
        runASingleTest(testname, loadedTests[testname])
      else :
        print(f"test [{testname}] not found")

def addListTests(theCli) :
  if 'testerMode' in config :
    if 0 < config['verbosity'] :
      print("Adding list tests command")
    @theCli.command('listTests',
      help="List all known tests",
      short_help="List all known tests"
    )
    def listTestsCallback(*args, **kwargs) :
      for aTestName, aTest in loadedTests.items() :
        print(aTestName)

def importCommands(cli) :
  """Import or load all python or yaml based click commands found in any
  of the commandsDirs directories."""

  commandsDirs = []
  if 'commandsDirs' in config : commandsDirs = config['commandsDirs']
  #commandsDirs.insert(0, 'cpcli/commands')
  for aCommandDir in commandsDirs :
    pkgPath = aCommandDir.replace('/','.')
    if aCommandDir.startswith('cpcli') :
      aCommandDir = os.path.join(os.path.dirname(__file__), aCommandDir.replace('cpcli/', ''))
    if not aCommandDir.startswith('/') :
      currentWD = os.path.abspath(os.getcwd())
      if currentWD not in sys.path :
        sys.path.insert(0, currentWD)
    loadPythonCommandsIn(aCommandDir, pkgPath, cli)
    loadYamlCommandsIn(aCommandDir, cli)
  addRunAllTests(cli)
  addRunTest(cli)
  addListTests(cli)

def getDataFromMajorDomo(method, url) :
  result = None
  try :
    http = HTTPUnixDomainConnection(config['socketPath'])
    http.request(method.upper(), url)
    result = json.loads(http.getresponse().read())
  except Exception as err :
    sys.stderr.write("\nERROR: Could not connect to a MajorDomo at [{}]\n".format(config['socketPath']))
    sys.stderr.write("  {}\n".format(repr(err)))

  return result