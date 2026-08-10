# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: PLR2004

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

    @abstractmethod
    def set_context(self, context: str) -> None:
        """
        Sets the context of this chooser.
        :param context: The context.
        """

    def get_options(self) -> dict[str, str]:
        """
        Retrieves a copy of the options of this chooser.
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
        return self._options.pop(key) if key in self._options else None

    def choose(self, default: str | None = None) -> str:
        """
        Prompts the user with this chooser. Blocks until the user submits their choice.\n
        No other presenter actions may be performed while this chooser is active.
        Must not be called while the underlying presenter is already blocked.\n
        The chooser may not be reused after this method has been called.
        :param default: The key of the default option to pre-select.
        :returns: The option key the user chose.
        """
        self._presenter.ensure_unblocked()

        if len(self._options) < 2:
            msg = "Chooser must have at least two options"
            raise ValueError(msg)
        if default is not None and default not in self._options:
            msg = f"Invalid default option, chooser has none with key {default}"
            raise ValueError(msg)
        return self._choose(default)

    @abstractmethod
    def _choose(self, default: str | None) -> str:
        pass

    def choose_multiple(self, default: list[str] | None = None, min_choices: int = 0, max_choices: int = -1,
                        incompatible_options: list[list[str]] | None = None) -> list[str]:
        """
        Prompts the user with this chooser, allowing multiple choices.
        Blocks until the user submits their choices.\n
        No other presenter actions may be performed while this chooser is active.
        Must not be called while the underlying presenter is already blocked.\n
        The chooser may not be reused after this method has been called.
        :param default: The keys of the default options to pre-select.
        :param min_choices: The minimum amount of choices the user must make.
        :param max_choices: The maximum amount of choices the user is allowed to make. ``-1`` is no limit.
        :param incompatible_options: A list of lists, containing keys of options that are incompatible with each other.
        :returns: A list containing the option keys the user chose.
        """
        self._presenter.ensure_unblocked()

        if len(self._options) < 2:
            msg = "Chooser must have at least two options"
            raise ValueError(msg)
        if default is not None:
            for key in default:
                if key not in self._options:
                    msg = f"Invalid default option, chooser has none with key {key}"
                    raise ValueError(msg)
        if min_choices < 0:
            msg = "min_choices cannot be less than zero"
            raise ValueError(msg)
        if max_choices != -1 and min_choices > max_choices:
            msg = "min_choices cannot be greater than max_choices"
            raise ValueError(msg)
        if max_choices > len(self._options):
            msg = "max_choices cannot be greater than the number of options"
            raise ValueError(msg)
        if 0 <= max_choices < 2:
            msg = "max_choices cannot be less than two"
            raise ValueError(msg)
        if incompatible_options is not None:
            for options in incompatible_options:
                if len(options) == 1:
                    msg = "incompatible_choices sublist cannot be empty"
                    raise ValueError(msg)
                seen_options: list[str] = []
                for option in options:
                    if option not in self._options:
                        msg = f"Invalid option in incompatible_choices, chooser has none with key {option}"
                        raise ValueError(msg)
                    if option in seen_options:
                        msg = f"Duplicate key in incompatible_choices: {option}"
                        raise ValueError(msg)
                    seen_options.append(option)
        if incompatible_options is not None and default is not None:
            default_set = set(default)
            for options in incompatible_options:
                intersection = default_set & set(options)
                if len(intersection) > 1:
                    msg = f"Default options contain incompatible options: {intersection}"
                    raise ValueError(msg)
        return self._choose_multiple(default, min_choices, max_choices, incompatible_options)

    @abstractmethod
    def _choose_multiple(self, default: list[str] | None, min_choices: int, max_choices: int,
                         incompatible_options: list[list[str]] | None) -> list[str]:
        pass
