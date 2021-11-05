# This file contains the projects command which interacts with the
# MajorDomo's projects interface.

import click
import yaml

from cpcli.utils import getDataFromMajorDomo

@click.command(
  short_help="list projects",
  help="List all projects known to the local MajorDomo.")
def projects() :
  print("Listing projects...")
  data = getDataFromMajorDomo('GET', '/projects')
  print("")
  print(yaml.dump(data))
  print("")
