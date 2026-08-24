# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import click

from abc import abstractmethod
from typing import Self, ClassVar
from sbcc_framework.feature import CompiledFeature, Feature
from sbcc_framework.presenter import Presenter


class Utility(Feature):
    """
    A feature utility without any state that can be executed.
    """

    REGISTRY: ClassVar[list[CompiledFeature[Self]]] = []

    @abstractmethod
    def run(self, presenter: Presenter) -> int | None:
        """
        Invoked when this utility is run by the user.
        :param presenter: The presenter to interact with the user.
        :return: The exit code to return when run in CLI mode, or `None`.
        """


class ComplexUtility(Feature):
    """
    A complex feature utility that can register custom commands and arguments.\n
    Only supported in CLI mode.
    """

    REGISTRY: ClassVar[list[CompiledFeature[Self]]] = []

    @abstractmethod
    def register(self, presenter: Presenter) -> click.Command:
        """
        Invoked when this utility is registered. Allows registering custom commands and arguments.
        :param presenter: The presenter to interact with the user.
        :return: The click command to register for this utility.
        """
