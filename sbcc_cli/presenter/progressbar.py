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
    active: bool = False
    progress: float = 0
    context: str | None = None
    printed_header: bool = False
    pulse: bool = False
    pulse_dir: int = 1
    pulse_pos: int = 0
    show_percentage: bool = False
    changed: bool = False
    render_interval: float = 0.1
    width: int = 50

    @override
    def _show(self) -> None:
        if self.active:
            msg = "Progressbar is already active"
            raise RuntimeError(msg)
        self.active = True

        self._presenter.block()
        print()
        if self.context is not None:
            self.__print_context()
            self.printed_header = True
        self.__print_bar()
        self.changed = False
        Thread(name="sbcc_cli:progressbar", target=self.__tick, daemon=True).start()

    @override
    def close(self) -> None:
        if not self.active:
            msg = "Progressbar is not active"
            raise RuntimeError(msg)
        self.active = False

        sys.stdout.write(ANSI_CURSOR_UP)
        sys.stdout.write(ANSI_CLEAR_LINE)
        if self.printed_header:
            sys.stdout.write(ANSI_CURSOR_UP)
            sys.stdout.write(ANSI_CLEAR_LINE)
        sys.stdout.write(ANSI_CURSOR_UP)
        self._presenter.unblock()

    @override
    def is_active(self) -> bool:
        return self.active

    @override
    def get_progress(self) -> float:
        return self.progress

    @override
    def set_progress(self, value: float) -> None:
        self.progress = min(value, 1)
        self.pulse = False
        self.changed = True

    @override
    def add_progress(self, value: float) -> None:
        self.set_progress(self.get_progress() + value)

    @override
    def get_context(self) -> str:
        return self.context if self.context is not None else ""

    @override
    def set_context(self, context: str) -> None:
        self.context = context if context != "" else None

    @override
    def get_pulse(self) -> bool:
        return self.pulse

    @override
    def set_pulse(self, mode: bool) -> None:
        self.pulse = mode
        self.changed = True

    @override
    def get_show_percentage(self) -> bool:
        return self.show_percentage

    @override
    def set_show_percentage(self, value: bool) -> None:
        self.show_percentage = value
        self.changed = True

    def __tick(self) -> None:
        while self.active:
            if self.changed or self.pulse:
                if self.printed_header:
                    sys.stdout.write(ANSI_CURSOR_UP)
                    sys.stdout.write(ANSI_CLEAR_LINE)

                sys.stdout.write(ANSI_CURSOR_UP)

                if self.context is not None:
                    sys.stdout.write(ANSI_CLEAR_LINE)
                    self.__print_context()
                    self.printed_header = True
                else:
                    self.printed_header = False

                sys.stdout.write(ANSI_CLEAR_LINE)
                self.__print_bar()

                self.changed = False
            sleep(self.render_interval)

    def __print_bar(self) -> None:
        print("[", end="")
        if not self.pulse:
            self.__print_bar_progress()
        else:
            self.__print_bar_pulse()
        print("]", end="")

        if self.show_percentage and not self.pulse:
            print(f" {(self.progress * 100):g}%")
        else:
            print()

    def __print_bar_progress(self) -> None:
        fill = int(self.progress * (self.width - 2))
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

    def __print_context(self) -> None:
        if self.context is None:
            msg = "Context is None"
            raise ValueError(msg)
        length = len(self.context)
        if self.context[-3:] == "...":
            # Context ending in "..." looks better if slightly centered more to the right,
            # as if dots not included.
            length -= 2
        print(" " * max(((self.width - length) // 2), 0) + self.context)
