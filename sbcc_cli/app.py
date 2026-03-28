# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The CLI application
"""

import click

from typing import Dict, Final
from click import Context, Group, pass_context
from sbcc_cli.presenter import CLIPresenter
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.toggle import ComplexToggle, Toggle
from sbcc_framework.feature.utility import ComplexUtility, Utility
from util import gettext_marker

_: Final = gettext_marker()


def add_category(command: click.Group, categories: Dict[str, Group], compiled: CompiledFeature):
    category_name = compiled.category.name
    if category_name not in categories:
        group = click.group(name=category_name, help=compiled.category.description)(lambda: None)
        categories[category_name] = group
        command.add_command(group)


class SBCCApplicationCLI:
    main_command: Group

    def __init__(self, main_command: Group):
        self.main_command = main_command

        self.register_toggles()
        self.register_utilities()

    def register_toggles(self):
        toggle_group = click.group(name="toggle", help=_("All available toggles"))(lambda: None)

        categories: Dict[str, Group] = {}

        for compiled in Toggle.REGISTRY:
            if not compiled.supports_cli() or not compiled.supports_environment():
                continue

            add_category(toggle_group, categories, compiled)

            feature_group = click.group(name=compiled.name, help=compiled.description)(lambda: None)
            categories[compiled.category.name].add_command(feature_group)

            @click.command(name="get", help=_("Prints the current state of this toggle"))
            @pass_context
            def getter(ctx: Context, *, __capture=compiled):
                unavailable_context = __capture.feature.is_available()
                if unavailable_context is not None:
                    print(_("The toggle '{0}' is not available:").format(__capture.display_name))
                    print(unavailable_context)
                    ctx.exit(1)

                state = "enabled" if __capture.feature.get_state() else "disabled"
                print(_("The feature '{0}' is currently {1}.").format(__capture.display_name, state))

            feature_group.add_command(getter)

            @click.command(name="set", help=_("Sets the state of this toggle"))
            @click.argument("mode", type=click.Choice(["on", "off"]))
            @pass_context
            def setter(ctx: Context, mode: str, *, __capture=compiled):
                unavailable_context = __capture.feature.is_available()
                if unavailable_context is not None:
                    print(_("The toggle '{0}' is not available:").format(__capture.display_name))
                    print(unavailable_context)
                    ctx.exit(1)

                mode_bool: bool = True if mode == "on" else False

                if __capture.feature.get_state() == mode_bool:
                    _mode = "enabled" if mode_bool else "disabled"
                    print(_("The toggle '{0}' is already {1}.").format(__capture.display_name, _mode))
                    ctx.exit(0)

                __capture.feature.set_state(CLIPresenter(), mode_bool)

            feature_group.add_command(setter)

        for complex_compiled in ComplexToggle.REGISTRY:
            if not complex_compiled.supports_cli() or not complex_compiled.supports_environment():
                continue

            add_category(toggle_group, categories, complex_compiled)

            feature_group = click.group(name=complex_compiled.name, help=complex_compiled.description)(lambda: None)
            categories[complex_compiled.category.name].add_command(feature_group)

            feature_getter = complex_compiled.feature.register_getter(CLIPresenter())
            feature_group.add_command(feature_getter, "get")

            feature_setter = complex_compiled.feature.register_setter(CLIPresenter())
            feature_group.add_command(feature_setter, "set")

        self.main_command.add_command(toggle_group)

    def register_utilities(self):
        utility_group = click.group(name="utility", help=_("All available utilities"))(lambda: None)

        categories: Dict[str, Group] = {}

        for compiled in Utility.REGISTRY:
            if not compiled.supports_cli() or not compiled.supports_environment():
                continue

            add_category(utility_group, categories, compiled)

            @click.command(name=compiled.name, help=compiled.description)
            @pass_context
            def utility(ctx: Context, *, __capture=compiled):
                unavailable_context = __capture.feature.is_available()
                if unavailable_context is not None:
                    print(_("The utility '{0}' is not available:").format(__capture.display_name))
                    print(unavailable_context)
                    ctx.exit(1)
                exit_code = __capture.feature.run(CLIPresenter())
                ctx.exit(exit_code if exit_code is not None else 0)

            categories[compiled.category.name].add_command(utility)

        for complex_compiled in ComplexUtility.REGISTRY:
            if not complex_compiled.supports_cli() or not complex_compiled.supports_environment():
                continue

            add_category(utility_group, categories, complex_compiled)

            utility = complex_compiled.feature.register(CLIPresenter())
            categories[complex_compiled.category.name].add_command(utility, name=complex_compiled.name)

        self.main_command.add_command(utility_group)
