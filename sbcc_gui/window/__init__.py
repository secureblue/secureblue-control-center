# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import cast
from gi.repository import Adw


class Toastable:
    """
    Utility interface to avoid circular dependencies. Must always be an Adw.ApplicationWindow.
    """

    def __init__(self) -> None:
        if not isinstance(self, Adw.ApplicationWindow):
            msg = "Toastable is not an Adw.ApplicationWindow"
            raise TypeError(msg)

    def show_toast(self, toast: Adw.Toast) -> None:
        raise NotImplementedError

    def get_window(self) -> Adw.ApplicationWindow:
        return cast(Adw.ApplicationWindow, cast(object, self))
