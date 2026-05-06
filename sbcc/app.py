# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
Main application entry point.
"""

import click

from typing import Final
from click import Context
from sbcc.features import load_features
from sbcc_cli.app import SBCCApplicationCLI
from sbcc_util import gettext_marker, has_gui, SBCC_VERSION

_: Final = gettext_marker()


@click.group(
    invoke_without_command=True,
    help="secureblue Control Center"
)
@click.option(
    "--version",
    "-v",
    help=_("Prints the version and exits."),
    is_flag=True
)
@click.pass_context
def launch(ctx: Context, gui: bool = False, version: bool = False) -> None:
    if gui and ctx.invoked_subcommand:
        print(_("Subcommands are not available when passing the '--gui' flag."))
        ctx.exit(1)

    if version:
        print(f"secureblue Control Center v{SBCC_VERSION}")
        ctx.exit(0)

    if gui:
        # Only attempt to load GUI if it is available
        from sbcc_gui.app import SBCCApplicationGUI
        SBCCApplicationGUI().run([])
        return

    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())
        ctx.exit(0)


# Only expose --gui flag if GUI is available
if has_gui():
    launch = click.option(
        "--gui",
        help=_("Launches the {0} graphical interface."
               "Can not be combined with other subcommands.").format("secureblue Control Center"),
        is_flag=True
    )(launch)

# Load and register all features
load_features()
# Initialize CLI application
SBCCApplicationCLI(launch)

if __name__ == "__main__":
    launch()
