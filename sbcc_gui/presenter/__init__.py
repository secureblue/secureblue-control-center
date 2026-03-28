# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from threading import Event
from typing import Any, Callable
from sbcc_framework import PresenterInterface
from sbcc_gui.presenter.chooser import GUIChooser
from sbcc_gui.presenter.progressbar import GUIProgressBar
from gi.repository import Adw, GLib
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.presenter import Chooser, Presenter, ProgressBar
from sbcc_gui.widget.dialog import BooleanDialog, InputDialog, TextDialog
from sbcc_gui.window import Toastable


@dataclasses.dataclass
class GUIPresenter(Presenter, PresenterInterface):
    main_window: Toastable
    compiled: CompiledFeature
    cancel_func: Callable[..., Any]

    def _show_text(self, text: str) -> None:
        GLib.idle_add(lambda: self.main_window.show_toast(Adw.Toast(
            title=text,
            timeout=5
        )))

    def _show_prompt_text(self, prompt_text: str) -> None:
        self.block()

        def show_dialog(text: str, _event: Event, _result: list[bool]):
            def cancel():
                _result[0] = False
                _event.set()

            dialog = TextDialog(heading=self.compiled.display_name, body=text, callback=lambda: _event.set(),
                                cancel_func=cancel)
            dialog.choose(self.main_window.get_window())

        result: list[bool] = [True]
        event = Event()
        GLib.idle_add(show_dialog, prompt_text, event, result)
        event.wait()

        if not result[0]:
            self.cancel_func()

        self.unblock()

    def _show_prompt_boolean(self, prompt_text: str) -> bool:
        self.block()

        def show_dialog(text: str, _event: Event, _result: list[bool]):
            def apply(choice: bool) -> None:
                _result[0] = choice
                _event.set()

            def cancel() -> None:
                _result[1] = False
                _event.set()

            dialog = BooleanDialog(heading=self.compiled.display_name, body=text, callback=apply, cancel_func=cancel)
            dialog.choose(self.main_window.get_window())

        result: list[bool] = [False, True]
        event = Event()
        GLib.idle_add(show_dialog, prompt_text, event, result)
        event.wait()

        if not result[1]:
            self.cancel_func()

        self.unblock()

        return result[0]

    def _show_prompt_input(self, prompt_text: str) -> str:
        self.block()

        def show_dialog(text: str, _event: Event, _result: list[Any]):
            def apply(choice: str) -> None:
                _result[0] = choice
                _event.set()

            def cancel() -> None:
                _result[1] = False
                _event.set()

            dialog = InputDialog(heading=self.compiled.display_name, body=text, callback=apply, cancel_func=cancel)
            dialog.choose(self.main_window.get_window())

        result: list[Any] = ["", True]
        event = Event()
        GLib.idle_add(show_dialog, prompt_text, event, result)
        event.wait()

        if not result[1]:
            self.cancel_func()

        self.unblock()

        return result[0]

    def create_progress_bar(self) -> ProgressBar:
        return GUIProgressBar(self, self.main_window, self.compiled)

    def create_chooser(self) -> Chooser:
        return GUIChooser(self, self.main_window, self.compiled)

    def is_blocked(self) -> bool:
        return self._blocked

    def cancel(self) -> None:
        self.cancel_func()
