# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import getpass
import sys

from typing import Final
from sbcc_cli.presenter.chooser import CLIChooser
from sbcc_cli.presenter.progressbar import CLIProgressBar
from sbcc_framework import PresenterInterface
from sbcc_framework.feature import BooleanResponse
from sbcc_framework.presenter import Presenter
from sbcc_framework.presenter.chooser import Chooser
from sbcc_framework.presenter.progressbar import ProgressBar
from util import gettext_marker, interruptible_ask

_: Final = gettext_marker()


ANSI_BLUE = "\033[94m"
ANSI_RED = "\033[91m"
ANSI_RESET = "\033[0m"
ANSI_CURSOR_UP = "\033[F"
ANSI_REMEMBER_CURSOR = "\0337"
ANSI_RESTORE_CURSOR = "\0338"


class CLIPresenter(Presenter, PresenterInterface):
    def _show_text(self, text: str) -> None:
        print(text)

    def _show_prompt_text(self, prompt_text: str) -> None:
        self.block()
        print(prompt_text)
        getpass.getpass(_("Press enter to continue..."))
        self.unblock()

    def _show_prompt_boolean(self, prompt_text: str, default: BooleanResponse, suggested: BooleanResponse,
                             destructive: BooleanResponse) -> bool:
        self.block()

        yes = "y" if default is not BooleanResponse.YES else "Y"
        no = "n" if default is not BooleanResponse.NO else "N"

        for response, appearance in [(suggested, ANSI_BLUE),
                                     (destructive, ANSI_RED)]:
            if response is BooleanResponse.YES:
                yes = appearance + yes + ANSI_RESET
            elif response is BooleanResponse.NO:
                no = appearance + no + ANSI_RESET

        prompt_banner = f"{prompt_text} [{yes}/{no}]: "
        while True:
            print(prompt_banner, end="")
            sys.stdout.write(ANSI_REMEMBER_CURSOR)
            choice = interruptible_ask("").lower().strip()
            if choice == "y":
                self.unblock()
                return True
            elif choice == "n":
                self.unblock()
                return False
            elif choice == "" and default is not BooleanResponse.NONE:
                sys.stdout.write(ANSI_RESTORE_CURSOR)
                print("y" if default is BooleanResponse.YES else "n")
                self.unblock()
                return default is BooleanResponse.YES
            else:
                print(_("Invalid input. Please enter y or n."))

    def _show_prompt_input(self, prompt_text: str) -> str:
        self.block()
        choice = interruptible_ask(prompt_text + ": ")
        self.unblock()
        return choice

    def _show_prompt_password(self, prompt_text: str) -> str:
        self.block()
        password = getpass.getpass(prompt_text + ": ")
        self.unblock()
        return password

    def create_progress_bar(self) -> ProgressBar:
        return CLIProgressBar(self)

    def create_chooser(self) -> Chooser:
        return CLIChooser(self)

    def is_blocked(self) -> bool:
        return self._blocked

    def cancel(self) -> None:
        pass
