# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: RET503

"""
The CLI application
"""

import click

from collections.abc import Callable
from dataclasses import field, dataclass
from typing import Final, Any, override
from click import Context, Group, pass_context, ParamType, Parameter
from click.shell_completion import CompletionItem
from sbcc_cli.presenter import CLIPresenter
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.preference import ComplexPreference, Preference, MultiPreference
from sbcc_framework.feature.utility import ComplexUtility, Utility
from sbcc_util import gettext_marker, ANSI_BLUE, ANSI_RESET

_: Final[Callable[[str], str]] = gettext_marker()


def _state_bool_to_str(value: bool) -> str:
    return _("enabled") if value else _("disabled")


@dataclass
class MultiPrefParamType(ParamType):
    name = "multi-pref"
    preference: MultiPreference
    options: dict[str, str] = field(default_factory=dict)

    def get_options(self) -> dict[str, str]:
        if len(self.options) == 0:
            self.options.update(self.preference.get_options())
        return self.options

    @override
    def convert(self, value: Any, param: Parameter | None, ctx: Context | None) -> Any:
        if value in self.get_options():
            return value
        else:
            self.fail(f"'{value}' is not one of " + ", ".join(f"'{k}'" for k in self.get_options()) + ".",
                      param, ctx)

    @override
    def get_metavar(self, param: Parameter, ctx: Context) -> str | None:
        return "{" + "|".join(self.get_options().keys()) + "}"

    @override
    def get_missing_message(self, param: Parameter, ctx: Context | None) -> str | None:
        return "Choose from:\n" + ",\n".join(f"\t{k} ({v})" for k, v in self.get_options().items())

    @override
    def shell_complete(self, ctx: Context, param: Parameter, incomplete: str) -> list[CompletionItem]:
        return [CompletionItem(value=opt) for opt in self.get_options() if opt.startswith(incomplete)]


class SBCCApplicationCLI:
    main_command: Group

    def __init__(self, main_command: Group):
        self.main_command = main_command

        self.__register_all_preferences()
        self.__register_all_utilities()

    def __register_all_preferences(self) -> None:
        pref_group = click.group(name="pref", help=_("All available preferences"))(lambda: None)
        categories: dict[str, Group] = {}

        self.__register_simple_preferences(pref_group, categories)
        self.__register_multi_preferences(pref_group, categories)
        self.__register_complex_preferences(pref_group, categories)

        self.main_command.add_command(pref_group)

    @classmethod
    def __register_simple_preferences(cls, pref_group: Group, categories: dict[str, Group]) -> None:
        for compiled in Preference.REGISTRY:
            if not compiled.supports_cli() or not compiled.supports_environment():
                continue

            cls.__add_category(pref_group, categories, compiled)

            feature_group = click.group(name=compiled.name, help=compiled.description)(lambda: None)
            categories[compiled.category.name].add_command(feature_group)

            @click.command(name="get", help=_("Prints the current state of this preference"))
            @pass_context
            def getter(ctx: Context, *, __capture: CompiledFeature[Preference] = compiled) -> None:
                unavailable_context = __capture.feature.is_available()
                if unavailable_context is not None:
                    print(_("The preference '{0}' is not available:").format(__capture.display_name))
                    print(unavailable_context)
                    ctx.exit(1)

                state = _state_bool_to_str(__capture.feature.get_state())
                print(_("The preference '{0}' is currently {1}.").format(__capture.display_name, state))

            feature_group.add_command(getter)

            @click.command(name="set", help=_("Sets the state of this preference"))
            @click.argument("state", type=click.Choice(["on", "off"]))
            @pass_context
            def setter(ctx: Context, state: str, *, __capture: CompiledFeature[Preference] = compiled) -> None:
                unavailable_context = __capture.feature.is_available()
                if unavailable_context is not None:
                    print(_("The preference '{0}' is not available:").format(__capture.display_name))
                    print(unavailable_context)
                    ctx.exit(1)

                old_state_bool = __capture.feature.get_state()
                new_state_bool = state == "on"

                if old_state_bool == new_state_bool:
                    new_state_str = _state_bool_to_str(new_state_bool)
                    print(_("The preference '{0}' is already {1}.").format(__capture.display_name, new_state_str))
                    ctx.exit(0)

                resulting_state_bool = __capture.feature.set_state(CLIPresenter(), new_state_bool)

                print()
                if old_state_bool == resulting_state_bool:
                    print(ANSI_BLUE + _("The preference '{0}' was not changed.")
                          .format(__capture.display_name) + ANSI_RESET)
                else:
                    resulting_state_str = _state_bool_to_str(resulting_state_bool)
                    print(ANSI_BLUE + _("The preference '{0}' was changed to {1}.")
                          .format(__capture.display_name, resulting_state_str) + ANSI_RESET)

            feature_group.add_command(setter)

    @classmethod
    def __register_multi_preferences(cls, pref_group: Group, categories: dict[str, Group]) -> None:
        for multi_compiled in MultiPreference.REGISTRY:
            if not multi_compiled.supports_cli() or not multi_compiled.supports_environment():
                continue

            cls.__add_category(pref_group, categories, multi_compiled)

            feature_group = click.group(name=multi_compiled.name, help=multi_compiled.description)(lambda: None)
            categories[multi_compiled.category.name].add_command(feature_group)

            @click.command(name="get", help=_("Prints the current state of this preference"))
            @pass_context
            def getter(ctx: Context, *, __capture: CompiledFeature[MultiPreference] = multi_compiled) -> None:
                unavailable_context = __capture.feature.is_available()
                if unavailable_context is not None:
                    print(_("The preference '{0}' is not available:").format(__capture.display_name))
                    print(unavailable_context)
                    ctx.exit(1)

                state = __capture.feature.get_state()
                print(_("The preference '{0}' is currently set to '{1}'.").format(__capture.display_name, state))

            feature_group.add_command(getter)

            @click.command(name="set", help=_("Sets the state of this preference"))
            @click.argument("state", type=MultiPrefParamType(multi_compiled.feature))
            @pass_context
            def setter(ctx: Context, state: str, *,
                       __capture: CompiledFeature[MultiPreference] = multi_compiled) -> None:
                unavailable_context = __capture.feature.is_available()
                if unavailable_context is not None:
                    print(_("The preference '{0}' is not available:").format(__capture.display_name))
                    print(unavailable_context)
                    ctx.exit(1)

                old_state = __capture.feature.get_state()

                if old_state == state:
                    print(_("The preference '{0}' is already set to '{1}'.").format(__capture.display_name, state))
                    ctx.exit(0)

                resulting_state = __capture.feature.set_state(CLIPresenter(), state)

                print()
                if old_state == resulting_state:
                    print(ANSI_BLUE + _("The preference '{0}' was not changed.")
                          .format(__capture.display_name) + ANSI_RESET)
                else:
                    print(ANSI_BLUE + _("The preference '{0}' was changed from '{1}' to '{2}'.")
                          .format(__capture.display_name, old_state, resulting_state) + ANSI_RESET)

            feature_group.add_command(setter)

    @classmethod
    def __register_complex_preferences(cls, pref_group: Group, categories: dict[str, Group]) -> None:
        for complex_compiled in ComplexPreference.REGISTRY:
            if not complex_compiled.supports_cli() or not complex_compiled.supports_environment():
                continue

            cls.__add_category(pref_group, categories, complex_compiled)

            feature_group = click.group(name=complex_compiled.name, help=complex_compiled.description)(lambda: None)
            categories[complex_compiled.category.name].add_command(feature_group)

            feature_getter = complex_compiled.feature.register_getter(CLIPresenter())
            feature_group.add_command(feature_getter, "get")

            feature_setter = complex_compiled.feature.register_setter(CLIPresenter())
            feature_group.add_command(feature_setter, "set")

    def __register_all_utilities(self) -> None:
        utility_group = click.group(name="utility", help=_("All available utilities"))(lambda: None)
        categories: dict[str, Group] = {}

        self.__register_simple_utilities(utility_group, categories)
        self.__register_complex_utilities(utility_group, categories)

        self.main_command.add_command(utility_group)

    @classmethod
    def __register_simple_utilities(cls, utility_group: Group, categories: dict[str, Group]) -> None:
        for compiled in Utility.REGISTRY:
            if not compiled.supports_cli() or not compiled.supports_environment():
                continue

            cls.__add_category(utility_group, categories, compiled)

            @click.command(name=compiled.name, help=compiled.description)
            @pass_context
            def utility(ctx: Context, *, __capture: CompiledFeature[Utility] = compiled) -> None:
                unavailable_context = __capture.feature.is_available()
                if unavailable_context is not None:
                    print(_("The utility '{0}' is not available:").format(__capture.display_name))
                    print(unavailable_context)
                    ctx.exit(1)
                __capture.feature.run(CLIPresenter())

            categories[compiled.category.name].add_command(utility)

    @classmethod
    def __register_complex_utilities(cls, utility_group: Group, categories: dict[str, Group]) -> None:
        for complex_compiled in ComplexUtility.REGISTRY:
            if not complex_compiled.supports_cli() or not complex_compiled.supports_environment():
                continue

            cls.__add_category(utility_group, categories, complex_compiled)

            utility = complex_compiled.feature.register(CLIPresenter())
            categories[complex_compiled.category.name].add_command(utility, name=complex_compiled.name)

    @classmethod
    def __add_category(cls, command: click.Group, categories: dict[str, Group], compiled: CompiledFeature) -> None:
        category_name = compiled.category.name
        if category_name not in categories:
            group = click.group(name=category_name, help=compiled.category.description)(lambda: None)
            categories[category_name] = group
            command.add_command(group)
