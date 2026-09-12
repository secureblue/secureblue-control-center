# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from dataclasses import dataclass
from sbcc_framework import PresenterLock


@dataclass
class ProgressBar(ABC):
    """
    A progress bar. Can show progress and a context above the progress bar.
    """

    _presenter: PresenterLock
    _active: bool = False
    _context: str | None = None
    _progress: float = 0
    _show_percentage: bool = False
    _pulse: bool = False

    def show(self) -> None:
        """
        Shows this progress bar to the user.\n
        No other presenter actions may be performed while this progress bar is active.
        Must not be called while the underlying presenter is already blocked.
        """
        self._presenter.ensure_unblocked()
        self._show()

    @abstractmethod
    def _show(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Closes this progress bar.\n
        The progress bar may not be reused after this method has been called.
        """

    def is_active(self) -> bool:
        """
        Retrieves whether this progress bar is active. (i.e. currently being shown to the user)
        :returns: Whether this progress bar is active.
        """
        return self._active

    def get_context(self) -> str | None:
        """
        Retrieves the context shown above the progress bar.
        :returns: The current context.
        """
        return self._context

    @abstractmethod
    def set_context(self, context: str | None) -> None:
        """
        Sets the context shown above the progress bar.
        :param context: The context to show.
        """

    def get_progress(self) -> float:
        """
        Retrieves the progress of this progress bar, from 0.0 to 1.0.
        :returns: The current progress.
        """
        return self._progress

    @abstractmethod
    def set_progress(self, value: float) -> None:
        """
        Sets the progress of this progress bar, from 0.0 to 1.0.
        :param value: The progress to show.
        """

    def add_progress(self, value: float) -> None:
        """
        Increments the progress of this progress bar.
        :param value: The progress to add.
        """
        self.set_progress(self.get_progress() + value)

    def get_show_percentage(self) -> bool:
        """
        Retrieves whether this progress bar should display its progress percentage.
        """
        return self._show_percentage

    @abstractmethod
    def set_show_percentage(self, value: bool) -> None:
        """
        Sets whether this progress bar should display its progress percentage. Defaults to false.
        :param value: Whether to show the progress percentage.
        """

    def get_pulse(self) -> bool:
        """
        Retrieves the pulse mode of this progress bar.
        :returns: The current pulse mode.
        """
        return self._pulse

    @abstractmethod
    def set_pulse(self, mode: bool) -> None:
        """
        Sets the pulse mode of this progress bar.\n
        In pulse mode no specific progress will be shown, useful to indicate loading of unknown progress.
        :param mode: The pulse mode (on/off).
        """
