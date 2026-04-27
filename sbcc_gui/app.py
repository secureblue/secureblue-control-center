# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The GUI application
"""

# We need to call require_version before importing the GTK libraries the first time.
# ruff: noqa: E402
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib
from typing import Final
from sbcc_framework.feature.utility import Utility
from sbcc_framework.feature.preference import Preference
from sbcc_gui.window.main import MainWindow
from util import gettext_marker

_: Final = gettext_marker()


class SBCCApplicationGUI(Adw.Application):
    main_window: MainWindow

    def __init__(self):
        super().__init__(application_id="dev.secureblue.controlcenter")
        GLib.set_application_name("secureblue Control Center")

    def do_activate(self) -> None:
        win = self.props.active_window
        if not win:
            self.main_window = MainWindow(application=self)

            self.register_preferences()
            self.register_utilities()

            win = self.main_window

        win.present()

    def register_preferences(self) -> None:
        for compiled in Preference.REGISTRY:
            if not compiled.supports_gui() or not compiled.supports_environment():
                continue
            self.main_window.add_preference(compiled)

    def register_utilities(self) -> None:
        for compiled in Utility.REGISTRY:
            if not compiled.supports_gui() or not compiled.supports_environment():
                continue
            self.main_window.add_utility(compiled)
