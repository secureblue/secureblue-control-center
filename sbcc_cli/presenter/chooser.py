# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Final
from sbcc_framework.presenter.chooser import Chooser
from util import gettext_marker, interruptible_ask

_: Final = gettext_marker()


class CLIChooser(Chooser):
    context: str | None = None

    def get_context(self) -> str:
        return self.context if self.context is not None else ""

    def set_context(self, context: str) -> None:
        self.context = context if context != "" else None

    def _choose(self) -> str:
        self._presenter.block()
        print()
        if self.context is not None:
            print(self.context)
        keys = list(self._options.keys())
        length = len(self._options)
        for i, display_name in enumerate(self._options.values()):
            print(f"\t{i + 1}) {display_name}")
        while True:
            selection = interruptible_ask(_("Choose an option [1-{0}]: ").format(length))
            if selection.isdigit() and 0 < int(selection) <= length:
                print()
                self._presenter.unblock()
                return keys[int(selection) - 1]
            print(_("Invalid selection. Please try again."))
