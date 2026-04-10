# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import sys

from threading import Thread
from time import sleep
from sbcc_framework.presenter.progressbar import ProgressBar


ANSI_CURSOR_UP = "\033[F"
ANSI_CLEAR_LINE = "\033[K"


class CLIProgressBar(ProgressBar):
    active: bool = False
    progress: float = 0
    context: str | None = None
    printed_header: bool = False
    pulse: bool = False
    pulse_dir: int = 1
    pulse_pos: int = 0
    changed: bool = False
    render_interval: float = 0.1
    width: int = 50

    def _show(self) -> None:
        if self.active:
            raise RuntimeError("ProgressBar is already active.")
        self.active = True

        self._presenter.block()
        print()
        if self.context is not None:
            self.print_context()
            self.printed_header = True
        self.print_bar()
        self.changed = False
        Thread(target=self.tick, daemon=True).start()

    def close(self) -> None:
        if not self.active:
            raise RuntimeError("ProgressBar is not active.")
        sys.stdout.write(ANSI_CURSOR_UP)
        sys.stdout.write(ANSI_CLEAR_LINE)
        if self.printed_header:
            sys.stdout.write(ANSI_CURSOR_UP)
            sys.stdout.write(ANSI_CLEAR_LINE)
        sys.stdout.write(ANSI_CURSOR_UP)
        self._presenter.unblock()
        self.active = False

    def is_active(self) -> bool:
        return self.active

    def get_progress(self) -> float:
        return self.progress

    def set_progress(self, value: float) -> None:
        self.progress = value
        self.pulse = False
        self.changed = True

    def add_progress(self, value: float) -> None:
        self.progress += value
        self.pulse = False
        self.changed = True

    def get_context(self) -> str:
        return self.context if self.context is not None else ""

    def set_context(self, context: str) -> None:
        self.context = context if context != "" else None

    def get_pulse(self) -> bool:
        return self.pulse

    def set_pulse(self, mode: bool) -> None:
        self.pulse = mode
        self.changed = True

    def tick(self) -> None:
        while self.active:
            if self.changed or self.pulse:
                if self.printed_header:
                    sys.stdout.write(ANSI_CURSOR_UP)
                    sys.stdout.write(ANSI_CLEAR_LINE)

                sys.stdout.write(ANSI_CURSOR_UP)

                if self.context is not None:
                    sys.stdout.write(ANSI_CLEAR_LINE)
                    self.print_context()
                    self.printed_header = True
                else:
                    self.printed_header = False

                sys.stdout.write(ANSI_CLEAR_LINE)
                self.print_bar()

                self.changed = False
            sleep(self.render_interval)

    def print_bar(self) -> None:
        print("[", end="")
        if not self.pulse:
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
        else:
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
        print("]")

    def print_context(self) -> None:
        if self.context is None:
            raise ValueError("Context is None.")
        length = len(self.context)
        if self.context[-3:] == "...":
            # Context ending in "..." looks better if slightly centered more to the right,
            # as if dots not included.
            length -= 2
        print(" " * max(((self.width - length) // 2), 0) + self.context)
