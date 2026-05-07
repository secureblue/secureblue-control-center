# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Event, Thread
from time import sleep
from gi.repository import GLib
from sbcc_framework import PresenterLock
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.presenter import ProgressBar
from sbcc_gui.widget.dialog import ProgressDialog
from sbcc_gui.window import Toastable


class GUIProgressBar(ProgressBar):
    main_window: Toastable
    compiled: CompiledFeature
    dialog: ProgressDialog
    # We cache states such that the getters don't have to be blocking
    active: bool = False
    progress: float = 0
    context: str = ""
    pulse: bool = False

    def __init__(self, presenter: PresenterLock, main_window: Toastable, compiled: CompiledFeature):
        super().__init__(presenter)

        self.main_window = main_window
        self.compiled = compiled

        def construct_dialog(_event: Event) -> None:
            self.dialog = ProgressDialog(heading=self.compiled.display_name)
            _event.set()

        event = Event()
        GLib.idle_add(construct_dialog, event)
        event.wait()

    def _show(self) -> None:
        if self.active:
            raise RuntimeError("ProgressBar is already active")
        self.active = True

        self._presenter.block()

        def apply_show(_event: Event) -> None:
            self.dialog.present(self.main_window.get_window())
            _event.set()

        event = Event()
        GLib.idle_add(apply_show, event)
        event.wait()

    def close(self) -> None:
        if not self.active:
            raise RuntimeError("ProgressBar is not active")
        self.active = False

        def apply_close(_event: Event) -> None:
            self.dialog.close()
            self._presenter.unblock()
            _event.set()

        event = Event()
        GLib.idle_add(apply_close, event)
        event.wait()

    def is_active(self) -> bool:
        return self.active

    def get_progress(self) -> float:
        return self.progress

    def set_progress(self, value: float) -> None:
        self.pulse = False

        def apply_progress(_value: float) -> None:
            self.dialog.get_progress_bar().set_fraction(_value)

        GLib.idle_add(apply_progress, value)
        self.progress = value

    def add_progress(self, value: float) -> None:
        new_value = self.get_progress() + value
        self.set_progress(new_value)

    def get_context(self) -> str:
        return self.context

    def set_context(self, context: str) -> None:
        def apply_context(_context: str) -> None:
            self.dialog.set_body(_context)

        GLib.idle_add(apply_context, context)
        self.context = context

    def get_pulse(self) -> bool:
        return self.pulse

    def set_pulse(self, mode: bool) -> None:
        if mode == self.pulse:
            return

        self.pulse = mode
        if mode:
            Thread(name="sbcc_gui:progressbar", target=self.tick_pulse, daemon=True).start()
        else:
            self.set_progress(self.progress)

    def tick_pulse(self) -> None:
        def apply_pulse() -> None:
            self.dialog.get_progress_bar().pulse()

        while self.active and self.pulse:
            GLib.idle_add(apply_pulse)
            sleep(0.2)
