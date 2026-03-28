# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import click

from abc import abstractmethod
from typing import List, Self
from sbcc_framework.feature import CompiledFeature, Feature
from sbcc_framework.presenter import Presenter


class Toggle(Feature):
    """
    A feature toggle with two states, enabled and disabled.
    """

    REGISTRY: List[CompiledFeature[Self]] = []

    @abstractmethod
    def get_state(self) -> bool:
        """
        Invoked when the toggle state is requested.
        :returns: The current toggle state.
        """
        pass

    @abstractmethod
    def set_state(self, presenter: Presenter, state: bool) -> bool:
        """
        Invoked when the user attempts to change the toggle state. Implement enable/disable logic here.
        :param presenter: The presenter to interact with the user.
        :param state: The requested new toggle state.
        :returns: The resulting new toggle state.
        """
        pass


class ComplexToggle(Feature):
    """
    A complex feature toggle with an arbitrary amount of states that can register custom commands and arguments.\n
    Only supported in CLI mode.
    """

    REGISTRY: List[CompiledFeature[Self]] = []

    @abstractmethod
    def register_getter(self, presenter: Presenter) -> click.Command:
        """
        Invoked when this toggle is registered. Allows registering custom commands and arguments
        for the getter of this toggle.
        :param presenter: The presenter to interact with the user.
        :returns: The click command to register for this toggle's getter.
        """
        pass

    @abstractmethod
    def register_setter(self, presenter: Presenter) -> click.Command:
        """
        Invoked when this toggle is registered. Allows registering custom commands and arguments
        for the setter of this toggle.
        :param presenter: The presenter to interact with the user.
        :returns: The click command to register for this toggle's setter.
        """
        pass
