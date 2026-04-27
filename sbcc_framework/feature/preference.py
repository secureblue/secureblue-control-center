# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import click

from abc import abstractmethod
from typing import List, Self
from sbcc_framework.feature import CompiledFeature, Feature
from sbcc_framework.presenter import Presenter


class Preference(Feature):
    """
    A feature preference with two states, enabled and disabled.
    """

    REGISTRY: List[CompiledFeature[Self]] = []

    @abstractmethod
    def get_state(self) -> bool:
        """
        Invoked when the current state is requested.
        :returns: The current state.
        """
        pass

    @abstractmethod
    def set_state(self, presenter: Presenter, state: bool) -> bool:
        """
        Invoked when the user attempts to change the state. Implement enable/disable logic here.
        :param presenter: The presenter to interact with the user.
        :param state: The requested new state.
        :returns: The resulting state.
        """
        pass


class ComplexPreference(Feature):
    """
    A complex feature preference that can register custom subcommands and arguments.\n
    Only supported in CLI mode.
    """

    REGISTRY: List[CompiledFeature[Self]] = []

    @abstractmethod
    def register_getter(self, presenter: Presenter) -> click.Command:
        """
        Invoked when this preference is registered. Allows registering custom subcommands and arguments
        for the getter of this preference.
        :param presenter: The presenter to interact with the user.
        :returns: The click command to register for this preference's getter.
        """
        pass

    @abstractmethod
    def register_setter(self, presenter: Presenter) -> click.Command:
        """
        Invoked when this preference is registered. Allows registering custom subcommands and arguments
        for the setter of this preference.
        :param presenter: The presenter to interact with the user.
        :returns: The click command to register for this preference's setter.
        """
        pass
