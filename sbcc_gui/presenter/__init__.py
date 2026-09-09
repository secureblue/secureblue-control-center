# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override
from gi.repository import Adw
from sbcc_framework import PresenterLock, Regex
from sbcc_framework.feature import CompiledFeature, BooleanResponse
from sbcc_framework.presenter import Chooser, Presenter, ProgressBar
from sbcc_gui import SyncResult, on_gtk_thread
from sbcc_gui.presenter.chooser import GUIChooser
from sbcc_gui.presenter.progressbar import GUIProgressBar
from sbcc_gui.widget.dialog import BooleanDialog, InputDialog, TextDialog, PasswordDialog
from sbcc_gui.window import Toastable
from sbcc_util import require_not_none


@dataclass
class GUIPresenter(PresenterLock, Presenter):
    main_window: Toastable
    compiled: CompiledFeature
    cancel_func: Callable[[], Any]

    @override
    @on_gtk_thread()
    def _show_text(self, text: str) -> None:
        self.main_window.show_toast(Adw.Toast(
            title=text,
            timeout=5
        ))

    @override
    def _show_prompt_text(self, prompt_text: str) -> None:
        self.block()

        @on_gtk_thread()
        def show_dialog(text: str, _sync: SyncResult) -> None:
            dialog = TextDialog(heading=self.compiled.display_name, body=text,
                                callback=_sync.set, cancel_func=_sync.cancel)
            dialog.choose(self.main_window.get_window())

        sync = SyncResult()
        show_dialog(prompt_text, sync)
        result = sync.get()

        if result.is_cancelled():
            self.cancel_func()

        self.unblock()

    @override
    def _show_prompt_boolean(self, prompt_text: str, default: BooleanResponse, suggested: BooleanResponse,
                             destructive: BooleanResponse) -> bool:
        self.block()

        @on_gtk_thread()
        def show_dialog(text: str, _sync: SyncResult[bool]) -> None:
            dialog = BooleanDialog(heading=self.compiled.display_name, body=text,
                                   default=default, suggested=suggested, destructive=destructive,
                                   callback=_sync.set, cancel_func=_sync.cancel)
            dialog.choose(self.main_window.get_window())

        sync = SyncResult[bool]()
        show_dialog(prompt_text, sync)
        result = sync.get()

        if result.is_cancelled():
            self.cancel_func()

        self.unblock()

        return require_not_none(result.value())

    @override
    def _show_prompt_input(self, prompt_text: str, prompt_regex: Regex | None) -> str:
        return self.__show_prompt_str(InputDialog, prompt_text, prompt_regex)

    @override
    def _show_prompt_password(self, prompt_text: str, prompt_regex: Regex | None) -> str:
        return self.__show_prompt_str(PasswordDialog, prompt_text, prompt_regex)

    def __show_prompt_str(self, dialog_type: type[InputDialog], prompt_text: str, prompt_regex: Regex | None) -> str:
        self.block()

        @on_gtk_thread()
        def show_dialog(text: str, _sync: SyncResult[str]) -> None:
            dialog = dialog_type(heading=self.compiled.display_name, body=text, regex=prompt_regex,
                                 callback=_sync.set, cancel_func=_sync.cancel)
            dialog.present(self.main_window.get_window())
            dialog.focus_input()

        sync = SyncResult[str]()
        show_dialog(prompt_text, sync)
        result = sync.get()

        if result.is_cancelled():
            self.cancel_func()

        self.unblock()

        return require_not_none(result.value())

    @override
    def create_progress_bar(self) -> ProgressBar:
        return GUIProgressBar(self, self.main_window, self.compiled)

    @override
    def create_chooser(self) -> Chooser:
        return GUIChooser(self, self.main_window, self.compiled)

    @override
    def cancel(self) -> None:
        self.cancel_func()
