# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import gettext
import importlib.util
import sys

from collections.abc import Callable
from typing import Final


SBCC_APPLICATION_ID: Final[str] = "dev.secureblue.controlcenter"
SBCC_VERSION: Final[str] = "1.0.0"
SBCC_WEBSITE: Final[str] = "https://secureblue.dev/"
SBCC_ISSUES_PAGE: Final[str] = "https://github.com/secureblue/secureblue-control-center/issues"


ANSI_BLUE: Final[str] = "\033[94m"
ANSI_RED: Final[str] = "\033[91m"
ANSI_RESET: Final[str] = "\033[0m"

ANSI_BACKGROUND_BLUE: Final[str] = "\033[44m"

ANSI_STRIKETHROUGH: Final[str] = "\033[9m"

ANSI_CURSOR_UP: Final[str] = "\033[F"
ANSI_CLEAR_LINE: Final[str] = "\033[K"

ANSI_REMEMBER_CURSOR: Final[str] = "\0337"
ANSI_RESTORE_CURSOR: Final[str] = "\0338"


def has_gui() -> bool:
    """
    Checks if the GUI is available in the current environment.
    :return: Whether the GUI is available.
    """
    return importlib.util.find_spec("sbcc_gui") is not None


def gettext_marker() -> Callable[[str], str]:
    """
    Retrieves the _ function used by gettext to mark translatable strings.
    """
    return gettext.translation("sbcc", "/usr/share/locale", fallback=True).gettext


def interruptible_ask(banner: str) -> str:
    """
    Retrieves input from the user, gracefully exiting if user interrupts.
    :param banner:
    :return:
    """
    response = None
    try:
        response = input(banner)
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(130)
    return response


def require_not_none[T](obj: T | None) -> T:
    """
    Convenience function to strip None-types in contexts where it is known to be impossible to occur.
    (or should raise an error if it does)
    """
    if obj is None:
        msg = "Illegal None value"
        raise ValueError(msg)
    return obj


class UserCancelFeatureException(Exception):  # noqa: N818
    """
    Gets raised to end thread execution when the user cancels a feature in the GUI.
    """
