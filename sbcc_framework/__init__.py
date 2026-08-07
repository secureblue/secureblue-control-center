# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The secureblue Control Center framework, providing a UI-agnostic, thread-safe API to interact with the user.
"""

import re


class PresenterLock:
    """
    Holds the lock for blocking presenters.
    """

    __blocked: bool = False

    def is_blocked(self) -> bool:
        return self.__blocked

    def block(self) -> None:
        self.__blocked = True

    def unblock(self) -> None:
        self.__blocked = False

    def cancel(self) -> None:
        raise NotImplementedError("Cancelling is not implemented for this presenter")


class Regex:
    """
    Holds a regular expression, optionally with context.
    """

    __pattern: re.Pattern
    __context: str | None

    def __init__(self, regex: str, context: str | None = None):
        """
        Creates a new regular expression, optionally with context.
        :param regex: The regular expression.
        :param context: Additional context to be shown to the user when the regular expression does not match.
        """
        self.__pattern = re.compile(regex)
        self.__context = context

    def has_context(self) -> bool:
        """
        Checks whether this regular expression has a context.
        :returns: Whether this regular expression has a context.
        """
        return self.__context is not None

    def get_context(self) -> str:
        """
        Retrieves the context of this regular expression.
        Will raise an error if this regular expression has no context.
        :returns: The context of this regular expression.
        """
        if self.__context is None:
            raise RuntimeError("Regex has no context")
        return self.__context

    def match(self, string: str) -> bool:
        """
        Matches the provided string against this regular expression. The string must fully match.
        :returns: True if the string fully matches, False otherwise.
        """
        return self.__pattern.fullmatch(string) is not None
