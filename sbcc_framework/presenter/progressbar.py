# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from abc import ABC, abstractmethod
from sbcc_framework import PresenterLock


@dataclasses.dataclass
class ProgressBar(ABC):
    """
    A progress bar. Can show progress and a context above the progress bar.
    """

    _presenter: PresenterLock

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

    @abstractmethod
    def is_active(self) -> bool:
        """
        Retrieves whether this progress bar is active. (i.e. currently being shown to the user)
        :returns: Whether this progress bar is active.
        """

    @abstractmethod
    def get_progress(self) -> float:
        """
        Retrieves the progress of this progress bar, from 0.0 to 1.0.
        :returns: The current progress.
        """

    @abstractmethod
    def set_progress(self, value: float) -> None:
        """
        Sets the progress of this progress bar, from 0.0 to 1.0.
        :param value: The progress to show.
        """

    @abstractmethod
    def add_progress(self, value: float) -> None:
        """
        Increments the progress of this progress bar.
        :param value: The progress to add.
        """

    @abstractmethod
    def get_context(self) -> str:
        """
        Retrieves the context shown above the progress bar.
        :returns: The current context.
        """

    @abstractmethod
    def set_context(self, context: str) -> None:
        """
        Sets the context shown above the progress bar.
        :param context: The context to show.
        """

    @abstractmethod
    def get_pulse(self) -> bool:
        """
        Retrieves the pulse mode of this progress bar.
        :return: The current pulse mode.
        """

    @abstractmethod
    def set_pulse(self, mode: bool) -> None:
        """
        Sets the pulse mode of this progress bar.\n
        In pulse mode no specific progress will be shown, useful to indicate loading of unknown progress.
        :param mode: The pulse mode (on/off).
        """

    @abstractmethod
    def get_show_percentage(self) -> bool:
        """
        Retrieves whether this progress bar should display its progress percentage.
        """

    @abstractmethod
    def set_show_percentage(self, value: bool) -> None:
        """
        Sets whether this progress bar should display its progress percentage. Defaults to false.
        :param value: Whether to show the progress percentage.
        """
