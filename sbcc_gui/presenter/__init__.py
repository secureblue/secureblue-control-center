# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from collections.abc import Callable
from threading import Event
from typing import Any, override
from gi.repository import Adw, GLib
from sbcc_framework import PresenterLock, Regex
from sbcc_framework.feature import CompiledFeature, BooleanResponse
from sbcc_framework.presenter import Chooser, Presenter, ProgressBar
from sbcc_gui.presenter.chooser import GUIChooser
from sbcc_gui.presenter.progressbar import GUIProgressBar
from sbcc_gui.widget.dialog import BooleanDialog, InputDialog, TextDialog, PasswordDialog
from sbcc_gui.window import Toastable


@dataclasses.dataclass
class GUIPresenter(PresenterLock, Presenter):
    main_window: Toastable
    compiled: CompiledFeature
    cancel_func: Callable[..., Any]

    @override
    def _show_text(self, text: str) -> None:
        GLib.idle_add(lambda: self.main_window.show_toast(Adw.Toast(
            title=text,
            timeout=5
        )))

    @override
    def _show_prompt_text(self, prompt_text: str) -> None:
        self.block()

        def show_dialog(text: str, _event: Event, _result: list[bool]) -> None:
            def cancel() -> None:
                _result[0] = False
                _event.set()

            dialog = TextDialog(heading=self.compiled.display_name, body=text, callback=_event.set,
                                cancel_func=cancel)
            dialog.choose(self.main_window.get_window())

        result: list[bool] = [True]
        event = Event()
        GLib.idle_add(show_dialog, prompt_text, event, result)
        event.wait()

        if not result[0]:
            self.cancel_func()

        self.unblock()

    @override
    def _show_prompt_boolean(self, prompt_text: str, default: BooleanResponse, suggested: BooleanResponse,
                             destructive: BooleanResponse) -> bool:
        self.block()

        def show_dialog(text: str, _event: Event, _result: list[bool]) -> None:
            def apply(choice: bool) -> None:
                _result[0] = choice
                _event.set()

            def cancel() -> None:
                _result[1] = False
                _event.set()

            dialog = BooleanDialog(heading=self.compiled.display_name, body=text, callback=apply, default=default,
                                   suggested=suggested, destructive=destructive, cancel_func=cancel)
            dialog.choose(self.main_window.get_window())

        result: list[bool] = [False, True]
        event = Event()
        GLib.idle_add(show_dialog, prompt_text, event, result)
        event.wait()

        if not result[1]:
            self.cancel_func()

        self.unblock()

        return result[0]

    @override
    def _show_prompt_input(self, prompt_text: str, prompt_regex: Regex | None) -> str:
        return self.__show_prompt_str(InputDialog, prompt_text, prompt_regex)

    @override
    def _show_prompt_password(self, prompt_text: str, prompt_regex: Regex | None) -> str:
        return self.__show_prompt_str(PasswordDialog, prompt_text, prompt_regex)

    def __show_prompt_str(self, dialog_type: type[InputDialog], prompt_text: str, prompt_regex: Regex | None) -> str:
        self.block()

        def show_dialog(text: str, _event: Event, _result: list[Any]) -> None:
            def apply(choice: str) -> None:
                _result[0] = choice
                _event.set()

            def cancel() -> None:
                _result[1] = False
                _event.set()

            dialog = dialog_type(heading=self.compiled.display_name, body=text, callback=apply, regex=prompt_regex,
                                 cancel_func=cancel)
            dialog.present(self.main_window.get_window())
            dialog.focus_input()

        result: list[Any] = ["", True]
        event = Event()
        GLib.idle_add(show_dialog, prompt_text, event, result)
        event.wait()

        if not result[1]:
            self.cancel_func()

        self.unblock()

        return result[0]

    @override
    def create_progress_bar(self) -> ProgressBar:
        return GUIProgressBar(self, self.main_window, self.compiled)

    @override
    def create_chooser(self) -> Chooser:
        return GUIChooser(self, self.main_window, self.compiled)

    @override
    def cancel(self) -> None:
        self.cancel_func()
