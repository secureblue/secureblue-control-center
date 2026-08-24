# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import click

from abc import abstractmethod
from typing import Self, ClassVar
from sbcc_framework.feature import CompiledFeature, Feature
from sbcc_framework.presenter import Presenter


class Preference(Feature):
    """
    A feature preference with two states, enabled and disabled.
    """

    REGISTRY: ClassVar[list[CompiledFeature[Self]]] = []

    @abstractmethod
    def get_state(self) -> bool:
        """
        Invoked when the current state of this preference is requested.
        :return: The current state.
        """

    @abstractmethod
    def set_state(self, presenter: Presenter, state: bool) -> bool:
        """
        Invoked when the user attempts to change the state of this preference.
        :param presenter: The presenter to interact with the user.
        :param state: The requested new state.
        :return: The resulting state.
        """


class MultiPreference(Feature):
    """
    A feature preference with an arbitrary amount of states.
    """

    REGISTRY: ClassVar[list[CompiledFeature[Self]]] = []

    @abstractmethod
    def get_options(self) -> dict[str, str]:
        """
        Invoked to register all valid states of this preference. The keys represent the valid states, the values are
        display names to those states.
        :return: A dictionary mapping each valid state to its display name.
        """

    @abstractmethod
    def get_state(self) -> str:
        """
        Invoked when the current state of this preference is requested.
        :return: The current state.
        """

    @abstractmethod
    def set_state(self, presenter: Presenter, state: str) -> str:
        """
        Invoked when the user attempts to change the state of this preference.
        :param presenter: The presenter to interact with the user.
        :param state: The requested new state.
        :return: The resulting state.
        """


class ComplexPreference(Feature):
    """
    A complex feature preference that can register custom subcommands and arguments.\n
    Only supported in CLI mode.
    """

    REGISTRY: ClassVar[list[CompiledFeature[Self]]] = []

    @abstractmethod
    def register_getter(self, presenter: Presenter) -> click.Command:
        """
        Invoked when this preference is registered. Allows registering custom subcommands and arguments
        for the getter of this preference.
        :param presenter: The presenter to interact with the user.
        :return: The click command to register for this preference's getter.
        """

    @abstractmethod
    def register_setter(self, presenter: Presenter) -> click.Command:
        """
        Invoked when this preference is registered. Allows registering custom subcommands and arguments
        for the setter of this preference.
        :param presenter: The presenter to interact with the user.
        :return: The click command to register for this preference's setter.
        """
