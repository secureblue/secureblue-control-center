# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Thread
from time import sleep
from typing import override
from gi.repository import GLib
from sbcc_framework import PresenterLock
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.presenter import ProgressBar
from sbcc_gui import on_gtk_thread
from sbcc_gui.widget.dialog import ProgressDialog
from sbcc_gui.window import Toastable


class GUIProgressBar(ProgressBar):
    main_window: Toastable
    compiled: CompiledFeature
    dialog: ProgressDialog
    pulse_thread: Thread | None = None

    def __init__(self, presenter: PresenterLock, main_window: Toastable, compiled: CompiledFeature):
        super().__init__(presenter)

        self.main_window = main_window
        self.compiled = compiled

        @on_gtk_thread(sync=True)
        def construct_dialog() -> None:
            self.dialog = ProgressDialog(heading=self.compiled.display_name)

        construct_dialog()

    @override
    def _show(self) -> None:
        if self._active:
            msg = "Progressbar is already active"
            raise RuntimeError(msg)
        self._active = True

        self._presenter.block()

        @on_gtk_thread(sync=True)
        def do_show() -> None:
            self.dialog.present(self.main_window.get_window())

        do_show()

        if self._pulse:
            self.__start_pulse_thread()

    @override
    def close(self) -> None:
        if not self._active:
            msg = "Progressbar is not active"
            raise RuntimeError(msg)
        self._active = False

        @on_gtk_thread(sync=True)
        def do_close() -> None:
            self.dialog.close()

        do_close()

        self._presenter.unblock()

    @override
    def set_context(self, context: str | None) -> None:
        self._context = context if context != "" else None
        GLib.idle_add(lambda: self.dialog.set_body(self._context if self._context is not None else ""))

    @override
    def set_progress(self, value: float) -> None:
        self._pulse = False
        self._progress = min(value, 1)
        GLib.idle_add(lambda: self.dialog.get_progress_bar().set_fraction(self._progress))

    @override
    def set_show_percentage(self, value: bool) -> None:
        self._show_percentage = value
        if not self._pulse:
            self.__set_show_percentage(self._show_percentage)

    @on_gtk_thread()
    def __set_show_percentage(self, value: bool) -> None:
        self.dialog.set_show_percentage(value)

    @override
    def set_pulse(self, mode: bool) -> None:
        if mode == self._pulse:
            return

        self._pulse = mode
        if self._pulse:
            if self._active:
                self.__start_pulse_thread()
        else:
            self.set_progress(self._progress)

    def __start_pulse_thread(self) -> None:
        if self.pulse_thread is None or not self.pulse_thread.is_alive():
            self.pulse_thread = Thread(name="sbcc_gui:progressbar:pulse", target=self.__tick_pulse, daemon=True).start()

    def __tick_pulse(self) -> None:
        if self._show_percentage:
            self.__set_show_percentage(False)

        while self._active and self._pulse:
            GLib.idle_add(lambda: self.dialog.get_progress_bar().pulse())
            sleep(0.2)

        if self._show_percentage:
            self.__set_show_percentage(True)
