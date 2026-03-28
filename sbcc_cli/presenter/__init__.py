# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import getpass

from typing import Final
from sbcc_cli.presenter.chooser import CLIChooser
from sbcc_cli.presenter.progressbar import CLIProgressBar
from sbcc_framework import PresenterInterface
from sbcc_framework.presenter import Presenter
from sbcc_framework.presenter.chooser import Chooser
from sbcc_framework.presenter.progressbar import ProgressBar
from util import gettext_marker, interruptible_ask

_: Final = gettext_marker()


class CLIPresenter(Presenter, PresenterInterface):
    def _show_text(self, text: str) -> None:
        print(text)

    def _show_prompt_text(self, prompt_text: str) -> None:
        self.block()
        print(prompt_text)
        getpass.getpass(_("Press enter to continue..."))
        self.unblock()

    def _show_prompt_boolean(self, prompt_text: str) -> bool:
        self.block()
        while True:
            choice = interruptible_ask(prompt_text + " [y/n]: ").lower().strip()
            if choice == "y":
                self.unblock()
                return True
            elif choice == "n":
                self.unblock()
                return False
            else:
                print(_("Invalid input. Please enter y or n."))

    def _show_prompt_input(self, prompt_text: str) -> str:
        self.block()
        choice = interruptible_ask(prompt_text + ": ")
        self.unblock()
        return choice

    def create_progress_bar(self) -> ProgressBar:
        return CLIProgressBar(self)

    def create_chooser(self) -> Chooser:
        return CLIChooser(self)

    def is_blocked(self) -> bool:
        return self._blocked

    def cancel(self) -> None:
        pass
