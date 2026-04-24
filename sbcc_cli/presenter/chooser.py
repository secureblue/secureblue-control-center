# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import sys

from typing import Final
from sbcc_framework.presenter.chooser import Chooser
from util import gettext_marker, interruptible_ask, ANSI_REMEMBER_CURSOR, ANSI_RESTORE_CURSOR

_: Final = gettext_marker()


class CLIChooser(Chooser):
    context: str | None = None

    def get_context(self) -> str:
        return self.context if self.context is not None else ""

    def set_context(self, context: str) -> None:
        self.context = context if context != "" else None

    def _choose(self, default: str | None) -> str:
        self._presenter.block()
        
        print()
        if self.context is not None:
            print(self.context)

        keys = list(self._options.keys())
        length = len(self._options)
        default_index: int | None = None
        for i, display_name in enumerate(self._options.values()):
            if default is not None and default == keys[i]:
                default_index = i + 1
            print(f"\t{i + 1}) {display_name}")

        default_banner_str = "" if default_index is None else f", default {default_index}"
        prompt_banner = _("Choose an option [1-{0}{1}]: ").format(length, default_banner_str)
        while True:
            print(prompt_banner, end="")
            sys.stdout.write(ANSI_REMEMBER_CURSOR)
            selection = interruptible_ask("").strip()
            if selection.isdigit() and 0 < int(selection) <= length:
                print()
                self._presenter.unblock()
                return keys[int(selection) - 1]
            elif default is not None and selection == "":
                sys.stdout.write(ANSI_RESTORE_CURSOR)
                print(default_index, end="\n\n")
                self._presenter.unblock()
                return default
            print(_("Invalid selection. Please try again."))
