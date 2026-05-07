# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from abc import ABC, abstractmethod
from dataclasses import field
from sbcc_framework import PresenterLock


@dataclasses.dataclass
class Chooser(ABC):
    """
    A chooser. Allows to prompt the user for a set of options.
    """

    _presenter: PresenterLock
    _options: dict[str, str] = field(default_factory=dict)

    @abstractmethod
    def get_context(self) -> str:
        """
        Retrieves the context of this chooser.
        :return: The context of this chooser.
        """
        pass

    @abstractmethod
    def set_context(self, context: str) -> None:
        """
        Sets the context of this chooser.
        :param context: The context.
        """
        pass

    def get_options(self) -> dict[str, str]:
        """
        Retrieves the options of this chooser.
        :return: A dictionary consisting of option keys mapped to their display names.
        """
        return self._options.copy()

    def add_option(self, key: str, name: str) -> None:
        """
        Adds an option to this chooser.
        :param key: The key of the option.
        :param name: The display name of the option.
        """
        self._options[key] = name

    def remove_option(self, key: str) -> str | None:
        """
        Removes an option from this chooser.
        :param key: The option key to remove.
        :return: The display name previously associated with the removed option, or None.
        """
        return self._options.pop(key) if self._options.__contains__(key) else None

    def choose(self, default: str | None = None) -> str:
        """
        Prompts the user with this chooser. Blocks until the user submits their choice.\n
        No other presenter actions may be performed while this chooser is active.
        Must not be called while the underlying presenter is already blocked.\n
        The chooser may not be reused after this method has been called.
        :param default: The key of the default option to pre-select.
        :returns: The option key the user chose.
        """
        if default is not None and default not in self._options:
            raise ValueError(f"Invalid default option, chooser has none with key {default}")
        if self._presenter.is_blocked():
            raise RuntimeError("Illegal action on blocked presenter")
        if not self._options:
            raise RuntimeError("Chooser has no options")
        return self._choose(default)

    @abstractmethod
    def _choose(self, default: str | None) -> str:
        pass
