# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The GUI-frontend implementation of the secureblue Control Center framework.
"""

from collections.abc import Callable
from threading import Event
from gi.repository import GLib
from sbcc_util import require_not_none


class Result[T]:
    __value: T | None
    __is_cancelled: bool

    def __init__(self, *, value: T | None = None, is_cancelled: bool = False) -> None:
        self.__value = value
        self.__is_cancelled = is_cancelled

    def value(self) -> T | None:
        return self.__value

    def is_cancelled(self) -> bool:
        return self.__is_cancelled


class SyncResult[T]:
    __result: Result[T] | None = None
    __event: Event

    def __init__(self):
        self.__event = Event()

    def set(self, value: T = None, /) -> None:
        self.__result = Result(value=value)
        self.__event.set()

    def cancel(self) -> None:
        self.__result = Result(is_cancelled=True)
        self.__event.set()

    def get(self) -> Result[T]:
        self.__event.wait()
        return require_not_none(self.__result)


def on_gtk_thread[**P, R](*, sync: bool = False) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """
    Ensures a function only runs on the GTK thread.
    :param sync: Whether to block and wait for execution on the GTK thread, if not already on it.
      If False, the function will always return None.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            if GLib.MainContext.default().is_owner():
                value = func(*args, **kwargs)
                if not sync:
                    return None
                return value
            else:  # noqa: PLR5501
                if sync:
                    def inner(_res: SyncResult[R]) -> None:
                        _res.set(func(*args, **kwargs))

                    res = SyncResult[R]()
                    GLib.idle_add(inner, res)

                    return res.get().value()
                else:
                    # inner function is needed to strip away return type of func.
                    # GLib.idle_add() runs functions repeatedly for as long as the
                    # return value is truthy.
                    def inner() -> None:
                        func(*args, **kwargs)

                    GLib.idle_add(inner)

                    return None
        return wrapper
    return decorator


class FeatureException(Exception):  # noqa: N818
    """
    Gets raised when an unexpected error occurs in a feature.
    """


class UserCancelFeatureException(FeatureException):
    """
    Gets raised to end feature-thread execution when the user cancels a feature.
    """
