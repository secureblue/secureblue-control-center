# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Event
from typing import Any, cast, override
from gi.repository import GLib
from sbcc_framework import PresenterLock
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.presenter import Chooser
from sbcc_gui.widget.dialog import ChooserDialog, MultiChooserDialog
from sbcc_gui.window import Toastable


class GUIChooser(Chooser):
    main_window: Toastable
    compiled: CompiledFeature
    context: str = ""

    def __init__(self, presenter: PresenterLock, main_window: Toastable, compiled: CompiledFeature):
        super().__init__(presenter)

        self.main_window = main_window
        self.compiled = compiled

    @override
    def get_context(self) -> str:
        return self.context

    @override
    def set_context(self, context: str) -> None:
        self.context = context

    @override
    def _choose(self, default: str | None) -> str:
        self._presenter.block()

        def show_dialog(_event: Event, _result: list[Any]) -> None:
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

    @override
    def _choose_multiple(self, default: list[str] | None, min_choices: int, max_choices: int,
                         incompatible_options: list[list[str]] | None) -> list[str]:
        self._presenter.block()

        def show_dialog(_event: Event, _result: list[Any]) -> None:
            def apply(choices: list[str]) -> None:
                cast(list[str], _result[0]).extend(choices)
                _event.set()

            def cancel() -> None:
                _result[1] = False
                _event.set()

            dialog = MultiChooserDialog(heading=self.compiled.display_name, body=self.context, callback=apply,
                                        min_choices=min_choices, max_choices=max_choices,
                                        incompatible_options=incompatible_options, cancel_func=cancel)

            for key, value in self._options.items():
                dialog.add_option(key, value)

            if default is not None:
                for default_option in default:
                    dialog.select_option(default_option)

            dialog.present(self.main_window.get_window())

        result: list[Any] = [[], True]
        event = Event()
        GLib.idle_add(show_dialog, event, result)
        event.wait()

        if not result[1]:
            self._presenter.cancel()

        self._presenter.unblock()

        return result[0]
