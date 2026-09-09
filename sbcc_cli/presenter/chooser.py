# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import readchar
import sys

from collections.abc import Callable
from getpass import getpass
from typing import Final, override
from sbcc_framework.presenter.chooser import Chooser
from sbcc_util import gettext_marker, ANSI_BACKGROUND_BLUE, ANSI_RESET, ANSI_CURSOR_UP, ANSI_CLEAR_LINE, \
    ANSI_STRIKETHROUGH, ANSI_RED

_: Final[Callable[[str], str]] = gettext_marker()


def _clear_lines(amount: int) -> None:
    for _ in range(amount):
        sys.stdout.write(ANSI_CLEAR_LINE)
        sys.stdout.write(ANSI_CURSOR_UP)


def _print_err_prompt(message: str) -> None:
    sys.stdout.write(ANSI_RED)
    print(message, end=_(" Press enter to continue. "))
    sys.stdout.write(ANSI_RESET)
    sys.stdout.flush()
    getpass("")


class CLIChooser(Chooser):
    context: str | None = None

    @override
    def get_context(self) -> str:
        return self.context if self.context is not None else ""

    @override
    def set_context(self, context: str) -> None:
        self.context = context if context != "" else None

    @override
    def _choose(self, default: str | None) -> str:
        self._presenter.block()

        print()
        if self.context is not None:
            print(self.context)

        keys = list(self._options.keys())
        length = len(self._options)

        cursor: int = 0 if default is None else -1
        while True:
            for i, display_name in enumerate(self._options.values()):
                if cursor is -1 and default == keys[i]:
                    cursor = i

                print("   >" if cursor == i else "    ", end=" ")
                print(f"{display_name}")

            print(_("Choose an option.\n"
                    "Use the arrow keys to choose an option and press enter to submit."))

            while True:
                selection = readchar.readkey()

                if selection == readchar.key.ENTER:
                    print()
                    self._presenter.unblock()
                    return keys[cursor]
                elif selection == readchar.key.UP:
                    if cursor == 0:
                        cursor = length - 1
                    else:
                        cursor -= 1
                    break
                elif selection == readchar.key.DOWN:
                    if cursor == length - 1:
                        cursor = 0
                    else:
                        cursor += 1
                    break

            _clear_lines(length + 2)

    @override
    def _choose_multiple(self, default: list[str] | None, min_choices: int, max_choices: int,
                         incompatible_options: list[list[str]] | None) -> list[str]:
        self._presenter.block()

        print()
        if self.context is not None:
            print(self.context)

        keys = list(self._options.keys())
        length = len(self._options)

        selected_options: list[str] = []
        if default is not None:
            selected_options.extend(default)

        disabled_options: list[str] = []
        cursor = 0
        loop = True
        while loop:
            if incompatible_options is not None:
                disabled_options.clear()
                for selected_option in selected_options:
                    for incompatible_options_sub in incompatible_options:
                        if selected_option in incompatible_options_sub:
                            disabled_options.extend(list(filter(
                                lambda e: e != selected_option,
                                incompatible_options_sub
                            )))

            for i, display_name in enumerate(self._options.values()):
                current_key = keys[i]
                disable = current_key in disabled_options or (len(selected_options) == max_choices
                                                              and current_key not in selected_options)
                highlight = current_key in selected_options

                print("   >" if cursor == i else "    ", end=" ")

                if highlight:
                    sys.stdout.write(ANSI_BACKGROUND_BLUE)
                elif disable:
                    sys.stdout.write(ANSI_STRIKETHROUGH)
                print(f"{display_name}")
                if highlight or disable:
                    sys.stdout.write(ANSI_RESET)

            prompt_banner = (_("You can select multiple options{0}. Selected options are highlighted.")
                             .format(_(" (up to {0})").format(max_choices) if max_choices != -1 else "")
                             + "\n" +
                             _("Use the arrow keys to choose an option, spacebar to (de-)select and enter to submit."))
            while True:
                print(prompt_banner)

                selection = readchar.readkey()

                if selection == readchar.key.ENTER:
                    if len(selected_options) < min_choices:
                        _print_err_prompt(_("You must select at least {0} option(s).").format(min_choices))
                        _clear_lines(1)
                    else:
                        loop = False
                        break
                elif selection == readchar.key.SPACE:
                    selected_option = keys[cursor]
                    if incompatible_options is not None and selected_option in disabled_options:
                        incompatible_causes: set[str] = set()
                        for incompatible_options_sub in incompatible_options:
                            if selected_option in incompatible_options_sub:
                                incompatible_causes.update(self._options[e] for e in
                                                           (set(incompatible_options_sub) & set(selected_options)))
                        _print_err_prompt(_("You can't select this option, as it is incompatible with the "
                                            "following already selected option(s): {0}.")
                                          .format(", ".join(f"'{e}'" for e in incompatible_causes)))
                        _clear_lines(1)
                    elif selected_option not in selected_options:
                        if max_choices != -1 and len(selected_options) == max_choices:
                            _print_err_prompt(_("You can't select more than {0} options.").format(max_choices))
                            _clear_lines(1)
                        else:
                            selected_options.append(selected_option)
                            break
                    else:
                        selected_options.remove(selected_option)
                        break
                elif selection == readchar.key.UP:
                    if cursor == 0:
                        cursor = length - 1
                    else:
                        cursor -= 1
                    break
                elif selection == readchar.key.DOWN:
                    if cursor == length - 1:
                        cursor = 0
                    else:
                        cursor += 1
                    break
                _clear_lines(2)

            if loop:
                _clear_lines(length + 2)

        print()

        self._presenter.unblock()
        return selected_options
