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
    active: bool = False
    progress: float = 0
    context: str = ""
    pulse: bool = False
    show_percentage: bool = False
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
        if self.active:
            msg = "Progressbar is already active"
            raise RuntimeError(msg)
        self.active = True

        self._presenter.block()

        @on_gtk_thread(sync=True)
        def do_show() -> None:
            self.dialog.present(self.main_window.get_window())

        do_show()

        if self.pulse:
            self.__start_pulse_thread()

    @override
    def close(self) -> None:
        if not self.active:
            msg = "Progressbar is not active"
            raise RuntimeError(msg)
        self.active = False

        @on_gtk_thread(sync=True)
        def do_close() -> None:
            self.dialog.close()

        do_close()

        self._presenter.unblock()

    @override
    def is_active(self) -> bool:
        return self.active

    @override
    def get_progress(self) -> float:
        return self.progress

    @override
    def set_progress(self, value: float) -> None:
        self.pulse = False
        self.progress = min(value, 1)
        GLib.idle_add(lambda: self.dialog.get_progress_bar().set_fraction(self.progress))

    @override
    def add_progress(self, value: float) -> None:
        self.set_progress(self.get_progress() + value)

    @override
    def get_context(self) -> str:
        return self.context

    @override
    def set_context(self, context: str) -> None:
        self.context = context
        GLib.idle_add(lambda: self.dialog.set_body(self.context))

    @override
    def get_pulse(self) -> bool:
        return self.pulse

    @override
    def set_pulse(self, mode: bool) -> None:
        if mode == self.pulse:
            return

        self.pulse = mode
        if self.pulse:
            if self.active:
                self.__start_pulse_thread()
        else:
            self.set_progress(self.progress)

    def __start_pulse_thread(self) -> None:
        if self.pulse_thread is None or not self.pulse_thread.is_alive():
            self.pulse_thread = Thread(name="sbcc_gui:progressbar", target=self.__tick_pulse, daemon=True).start()

    def __tick_pulse(self) -> None:
        if self.show_percentage:
            self.__set_show_percentage(False)

        while self.active and self.pulse:
            GLib.idle_add(lambda: self.dialog.get_progress_bar().pulse())
            sleep(0.2)

        if self.show_percentage:
            self.__set_show_percentage(True)

    @override
    def get_show_percentage(self) -> bool:
        return self.show_percentage

    @override
    def set_show_percentage(self, value: bool) -> None:
        self.show_percentage = value
        if not self.pulse:
            self.__set_show_percentage(self.show_percentage)

    @on_gtk_thread()
    def __set_show_percentage(self, value: bool) -> None:
        self.dialog.set_show_percentage(value)
