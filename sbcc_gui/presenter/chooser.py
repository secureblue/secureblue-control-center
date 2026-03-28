# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Event
from typing import Any
from sbcc_framework import PresenterInterface
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.presenter import Chooser
from sbcc_gui.widget.dialog import ChooserDialog
from sbcc_gui.window import Toastable
from gi.repository import GLib


class GUIChooser(Chooser):
    main_window: Toastable
    compiled: CompiledFeature
    dialog: ChooserDialog
    # We cache states such that the getters don't have to be blocking
    context: str = ""

    def __init__(self, presenter: PresenterInterface, main_window: Toastable, compiled: CompiledFeature):
        super().__init__(presenter)

        self.main_window = main_window
        self.compiled = compiled

        self.dialog = ChooserDialog(heading=self.compiled.display_name)

    def get_context(self) -> str:
        return self.context

    def set_context(self, context: str) -> None:
        def apply_context(_context: str) -> None:
            self.dialog.set_body(_context)

        GLib.idle_add(apply_context, context)
        self.context = context

    def _choose(self) -> str:
        self._presenter.block()

        def show_dialog(_event: Event, _result: list[Any]):
            def apply(choice: str) -> None:
                _result[0] = choice
                _event.set()

            def cancel() -> None:
                _result[1] = False
                _event.set()

            for key, value in self._options.items():
                self.dialog.add_option(key, value)

            self.dialog.choose_callback(self.main_window.get_window(), apply, cancel)

        result: list[Any] = ["", True]
        event = Event()
        GLib.idle_add(show_dialog, event, result)
        event.wait()

        if not result[1]:
            self._presenter.cancel()

        self._presenter.unblock()

        return result[0]
