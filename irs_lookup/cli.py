import click
import click_log
from dotenv import load_dotenv
import os
from pathlib import Path

import irs_lookup.io as _io
import irs_lookup.lookup_irs as _lookup
from .log import logger


@click.command(name="fetch-990s", help="Load 990 data for a given ein(s)")
@click.option('--ein', '-e', multiple=True, help='eins')
@click.option("--ein-file", type=click.Path(exists=True),
              help="list of eins, broken by newline")
@click.option("--output", type=click.Path(), default="%s/output" % (os.getcwd()),
              help="output folder for ein data")
def cli_fetch_990s(ein, ein_file, output):
    Path(output).mkdir(parents=True, exist_ok=True)

    eins = []

    # for ein in f:
    #     data =
    if len(ein) > 0:
        eins = ein
    elif ein_file:
        with open(ein_file) as f:
            eins = f.readlines()

    df = _lookup.lookup_990s(eins)
    _io.write_dataframe(df, filename="output", directory=output)


@click_log.simple_verbosity_option(logger)
@click.group()
@click.option("--env-file", type=click.Path(exists=True),
              help="env file to load environment variables from")
def cli(env_file):
    if env_file is None:
        env_file = os.path.join(os.getcwd(), '.env')

    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file)


cli.add_command(cli_fetch_990s)
