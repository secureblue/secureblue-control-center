# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import sys

from threading import Thread
from time import sleep
from typing import override
from sbcc_framework.presenter.progressbar import ProgressBar
from sbcc_util import ANSI_CURSOR_UP, ANSI_CLEAR_LINE


class CLIProgressBar(ProgressBar):
    printed_header: bool = False
    pulse_dir: int = 1
    pulse_pos: int = 0
    changed: bool = False
    render_interval: float = 0.1
    width: int = 50

    @override
    def _show(self) -> None:
        if self._active:
            msg = "Progressbar is already active"
            raise RuntimeError(msg)
        self._active = True

        self._presenter.block()
        print()
        if self._context is not None:
            self.__print_context()
            self.printed_header = True
        self.__print_bar()
        self.changed = False
        Thread(name="sbcc_cli:progressbar", target=self.__tick, daemon=True).start()

    @override
    def close(self) -> None:
        if not self._active:
            msg = "Progressbar is not active"
            raise RuntimeError(msg)
        self._active = False

        sys.stdout.write(ANSI_CURSOR_UP)
        sys.stdout.write(ANSI_CLEAR_LINE)
        if self.printed_header:
            sys.stdout.write(ANSI_CURSOR_UP)
            sys.stdout.write(ANSI_CLEAR_LINE)
        sys.stdout.write(ANSI_CURSOR_UP)
        self._presenter.unblock()

    @override
    def set_context(self, context: str | None) -> None:
        self._context = context if context != "" else None

    @override
    def set_progress(self, value: float) -> None:
        self._progress = min(value, 1)
        self._pulse = False
        self.changed = True

    @override
    def set_show_percentage(self, value: bool) -> None:
        self._show_percentage = value
        self.changed = True

    @override
    def set_pulse(self, mode: bool) -> None:
        self._pulse = mode
        self.changed = True

    def __tick(self) -> None:
        while self._active:
            if self.changed or self._pulse:
                if self.printed_header:
                    sys.stdout.write(ANSI_CURSOR_UP)
                    sys.stdout.write(ANSI_CLEAR_LINE)

                sys.stdout.write(ANSI_CURSOR_UP)

                if self._context is not None:
                    sys.stdout.write(ANSI_CLEAR_LINE)
                    self.__print_context()
                    self.printed_header = True
                else:
                    self.printed_header = False

                sys.stdout.write(ANSI_CLEAR_LINE)
                self.__print_bar()

                self.changed = False
            sleep(self.render_interval)

    def __print_context(self) -> None:
        if self._context is None:
            msg = "Context is None"
            raise ValueError(msg)
        length = len(self._context)
        if self._context[-3:] == "...":
            # Context ending in "..." looks better if slightly centered more to the right,
            # as if dots not included.
            length -= 2
        print(" " * max(((self.width - length) // 2), 0) + self._context)

    def __print_bar(self) -> None:
        print("[", end="")
        if not self._pulse:
            self.__print_bar_progress()
        else:
            self.__print_bar_pulse()
        print("]", end="")

        if self._show_percentage and not self._pulse:
            print(f" {(self._progress * 100):g}%")
        else:
            print()

    def __print_bar_progress(self) -> None:
        fill = int(self._progress * (self.width - 2))
        for i in range(self.width - 2):
            char: str
            if i < fill:
                char = "="
            elif i == fill:
                char = ">"
            else:
                char = "."
            print(char, end="")

    def __print_bar_pulse(self) -> None:
        draw_range = self.width - 2
        for i in range(draw_range):
            char: str
            if i == self.pulse_pos:
                char = "<"
            elif self.pulse_pos < i <= self.pulse_pos + 3:
                char = "="
            elif i == self.pulse_pos + 4:
                char = ">"
            else:
                char = "."
            print(char, end="")
        if ((self.pulse_dir == 1 and self.pulse_pos == draw_range - 5)
                or (self.pulse_dir == -1 and self.pulse_pos == 0)):
            self.pulse_dir = -self.pulse_dir
        self.pulse_pos += self.pulse_dir
