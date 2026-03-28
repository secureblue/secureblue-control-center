# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from sbcc_framework.presenter.chooser import Chooser
from sbcc_framework.presenter.progressbar import ProgressBar


class Presenter(ABC):
    """
    Base class for presenters, providing a UI-agnostic API to interact with the user.
    """

    def show_text(self, text: str) -> None:
        """
        Shows text to the user. May be ephemeral.\n
        Must not be called while the presenter is blocked.
        :param text: The text to show.
        """
        self._ensure_unblocked()
        self._show_text(text)

    @abstractmethod
    def _show_text(self, text: str) -> None:
        pass

    def show_prompt_text(self, prompt_text: str) -> None:
        """
        Shows text to the user that must be acknowledged. Blocks until acknowledgement is given.\n
        Must not be called while the presenter is blocked.
        :param prompt_text: The prompt text to show.
        """
        self._ensure_unblocked()
        self._show_prompt_text(prompt_text)

    @abstractmethod
    def _show_prompt_text(self, prompt_text: str) -> None:
        pass

    def show_prompt_boolean(self, prompt_text: str) -> bool:
        """
        Shows a yes/no prompt to the user. Blocks until the user made their choice.\n
        Must not be called while the presenter is blocked.
        :param prompt_text: The prompt text to show.
        :returns: The user choice.
        """
        self._ensure_unblocked()
        return self._show_prompt_boolean(prompt_text)

    @abstractmethod
    def _show_prompt_boolean(self, prompt_text: str) -> bool:
        pass

    def show_prompt_input(self, prompt_text: str) -> str:
        """
        Prompts the user for input. Blocks until the user submits their input.\n
        Must not be called while the presenter is blocked.
        :param prompt_text: The prompt text to show.
        :returns: The user input.
        """
        self._ensure_unblocked()
        return self._show_prompt_input(prompt_text)

    @abstractmethod
    def _show_prompt_input(self, prompt_text: str) -> str:
        pass

    @abstractmethod
    def create_progress_bar(self) -> ProgressBar:
        """
        Creates a new progress bar.
        :returns: The new progress bar.
        """
        pass

    @abstractmethod
    def create_chooser(self) -> Chooser:
        """
        Creates a new chooser.
        :returns: The new chooser.
        """
        pass

    @abstractmethod
    def is_blocked(self) -> bool:
        """
        Retrieves whether this presenter is currently blocked.
        :return: Whether this presenter is blocked.
        """
        pass

    def _ensure_unblocked(self) -> None:
        if self.is_blocked():
            raise RuntimeError("Illegal call on blocked presenter")
