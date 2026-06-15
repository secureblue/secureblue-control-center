# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import gettext
import importlib.util
import sys

from typing import Callable, Final, TypeVar

SBCC_APPLICATION_ID: Final = "dev.secureblue.controlcenter"
SBCC_VERSION: Final = "1.0.0"
SBCC_WEBSITE: Final = "https://secureblue.dev/"
SBCC_ISSUES_PAGE: Final = "https://github.com/secureblue/secureblue-control-center/issues"


ANSI_BLUE: Final = "\033[94m"
ANSI_RED: Final = "\033[91m"
ANSI_RESET: Final = "\033[0m"

ANSI_CURSOR_UP: Final = "\033[F"
ANSI_CLEAR_LINE: Final = "\033[K"

ANSI_REMEMBER_CURSOR: Final = "\0337"
ANSI_RESTORE_CURSOR: Final = "\0338"


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


T = TypeVar("T")


def require_not_none(obj: T | None) -> T:
    """
    Convenience function to strip None-types in contexts where it is known to be impossible to occur.
    (or should raise an error if it does)
    """
    if obj is None:
        raise ValueError("Illegal None value")
    return obj


class UserCancelFeatureException(Exception):
    """
    Gets raised to end thread execution when the user cancels a feature in the GUI.
    """
    pass
