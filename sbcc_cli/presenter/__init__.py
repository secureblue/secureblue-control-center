# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import getpass
import sys

from collections.abc import Callable
from typing import Final, override
from sbcc_cli.presenter.chooser import CLIChooser
from sbcc_cli.presenter.progressbar import CLIProgressBar
from sbcc_framework import PresenterLock, Regex
from sbcc_framework.feature import BooleanResponse
from sbcc_framework.presenter import Presenter
from sbcc_framework.presenter.chooser import Chooser
from sbcc_framework.presenter.progressbar import ProgressBar
from sbcc_util import gettext_marker, interruptible_ask, ANSI_BLUE, ANSI_RED, ANSI_RESET, ANSI_REMEMBER_CURSOR, \
    ANSI_RESTORE_CURSOR

_: Final[Callable[[str], str]] = gettext_marker()


def _prompt_until_valid(prompt_func: Callable[[str], str], prompt_text: str, prompt_regex: Regex | None) -> str:
    while True:
        choice = prompt_func(prompt_text + ": ")
        if prompt_regex is None or prompt_regex.match(choice):
            break
        else:
            sys.stdout.write(ANSI_RED)
            print(
                _("Input does not match required pattern.")
                if prompt_regex is None or not prompt_regex.has_context()
                else _("Invalid input: {0}").format(prompt_regex.get_context())
            )
            sys.stdout.write(ANSI_RESET)
            sys.stdout.flush()
    return choice


class CLIPresenter(PresenterLock, Presenter):
    @override
    def _show_text(self, text: str) -> None:
        print(text)

    @override
    def _show_prompt_text(self, prompt_text: str) -> None:
        self.block()
        print(prompt_text)
        getpass.getpass(_("Press enter to continue..."))
        self.unblock()

    @override
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

    @override
    def _show_prompt_input(self, prompt_text: str, prompt_regex: Regex | None) -> str:
        self.block()
        choice = _prompt_until_valid(interruptible_ask, prompt_text, prompt_regex)
        self.unblock()
        return choice

    @override
    def _show_prompt_password(self, prompt_text: str, prompt_regex: Regex | None) -> str:
        self.block()
        password = _prompt_until_valid(getpass.getpass, prompt_text, prompt_regex)
        self.unblock()
        return password

    @override
    def create_progress_bar(self) -> ProgressBar:
        return CLIProgressBar(self)

    @override
    def create_chooser(self) -> Chooser:
        return CLIChooser(self)
