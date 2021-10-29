# This file contains an example of defining python methods which *are*
# click commands.

# Any methods which are decorated using the '@click.command' decorator
# *will* be visible from the cpcli help system.

import click

@click.command(short_help="An example test function")
def exampleTestFunc() :
  pass
