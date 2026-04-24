# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Event
from typing import Any
from gi.repository import GLib
from sbcc_framework import PresenterInterface
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.presenter import Chooser
from sbcc_gui.widget.dialog import ChooserDialog
from sbcc_gui.window import Toastable


class GUIChooser(Chooser):
    main_window: Toastable
    compiled: CompiledFeature
    context: str = ""

    def __init__(self, presenter: PresenterInterface, main_window: Toastable, compiled: CompiledFeature):
        super().__init__(presenter)

        self.main_window = main_window
        self.compiled = compiled

    def get_context(self) -> str:
        return self.context

    def set_context(self, context: str) -> None:
        self.context = context

    def _choose(self, default: str | None) -> str:
        self._presenter.block()

        def show_dialog(_event: Event, _result: list[Any]):
            def apply(choice: str) -> None:
                _result[0] = choice
                _event.set()

            def cancel() -> None:
                _result[1] = False
                _event.set()

            dialog = ChooserDialog(heading=self.compiled.display_name, body=self.context, callback=apply,
                                   cancel_func=cancel)

            for key, value in self._options.items():
                dialog.add_option(key, value)

            # select default option if provided, otherwise select first option
            dialog.select_option(default if default is not None else next(iter(self._options.keys())))

            dialog.choose(self.main_window.get_window())

        result: list[Any] = ["", True]
        event = Event()
        GLib.idle_add(show_dialog, event, result)
        event.wait()

        if not result[1]:
            self._presenter.cancel()

        self._presenter.unblock()

        return result[0]
