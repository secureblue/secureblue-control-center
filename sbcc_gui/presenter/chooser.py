# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import override
from sbcc_framework import PresenterLock
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.presenter import Chooser
from sbcc_gui import SyncResult, on_gtk_thread
from sbcc_gui.widget.dialog import ChooserDialog, MultiChooserDialog
from sbcc_gui.window import Toastable
from sbcc_util import require_not_none


class GUIChooser(Chooser):
    main_window: Toastable
    compiled: CompiledFeature

    def __init__(self, presenter: PresenterLock, main_window: Toastable, compiled: CompiledFeature):
        super().__init__(presenter)

        self.main_window = main_window
        self.compiled = compiled

    @override
    def _choose(self, default: str | None) -> str:
        self._presenter.block()

        @on_gtk_thread()
        def show_dialog(_sync: SyncResult[str]) -> None:
            context = self._context if self._context is not None else ""
            dialog = ChooserDialog(heading=self.compiled.display_name, body=context,
                                   callback=_sync.set, cancel_func=_sync.cancel)

            for key, value in self._options.items():
                dialog.add_option(key, value)

            # select default option if provided, otherwise select first option
            dialog.select_option(default if default is not None else next(iter(self._options.keys())))

            dialog.choose(self.main_window.get_window())

        sync = SyncResult[str]()
        show_dialog(sync)
        result = sync.get()

        if result.is_cancelled():
            self._presenter.cancel()

        self._presenter.unblock()

        return require_not_none(result.value())

    @override
    def _choose_multiple(self, default: list[str] | None, min_choices: int, max_choices: int,
                         incompatible_options: list[list[str]] | None) -> list[str]:
        self._presenter.block()

        @on_gtk_thread()
        def show_dialog(_sync: SyncResult[list[str]]) -> None:
            context = self._context if self._context is not None else ""
            dialog = MultiChooserDialog(heading=self.compiled.display_name, body=context,
                                        min_choices=min_choices, max_choices=max_choices,
                                        incompatible_options=incompatible_options,
                                        callback=_sync.set, cancel_func=_sync.cancel)

            for key, value in self._options.items():
                dialog.add_option(key, value)

            if default is not None:
                for default_option in default:
                    dialog.select_option(default_option)

            dialog.present(self.main_window.get_window())

        sync = SyncResult[list[str]]()
        show_dialog(sync)
        result = sync.get()

        if result.is_cancelled():
            self._presenter.cancel()

        self._presenter.unblock()

        return require_not_none(result.value())
