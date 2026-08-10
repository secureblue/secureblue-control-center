# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from sbcc_framework import Regex
from sbcc_framework.feature import BooleanResponse
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
        self.ensure_unblocked()
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
        self.ensure_unblocked()
        self._show_prompt_text(prompt_text)

    @abstractmethod
    def _show_prompt_text(self, prompt_text: str) -> None:
        pass

    def show_prompt_boolean(self, prompt_text: str, default: BooleanResponse = BooleanResponse.NONE,
                            suggested: BooleanResponse = BooleanResponse.NONE,
                            destructive: BooleanResponse = BooleanResponse.NONE) -> bool:
        """
        Shows a yes/no prompt to the user. Blocks until the user made their choice.\n
        Must not be called while the presenter is blocked.
        :param prompt_text: The prompt text to show.
        :param default: The default response to pre-select.
        :param suggested: The suggested response to highlight. Should be used to indicate safe responses, or equivalent.
        :param destructive: The destructive response to highlight. Should be used to indicate dangerous responses,
          or equivalent.
        :returns: The user choice.
        """
        self.ensure_unblocked()
        if suggested is not BooleanResponse.NONE and suggested == destructive:
            msg = "Suggested and destructive responses cannot be the same."
            raise ValueError(msg)
        return self._show_prompt_boolean(prompt_text, default, suggested, destructive)

    @abstractmethod
    def _show_prompt_boolean(self, prompt_text: str, default: BooleanResponse, suggested: BooleanResponse,
                             destructive: BooleanResponse) -> bool:
        pass

    def show_prompt_input(self, prompt_text: str, prompt_regex: Regex | None = None) -> str:
        """
        Prompts the user for input. Blocks until the user submits their input.\n
        Must not be called while the presenter is blocked.
        :param prompt_text: The prompt text to show.
        :param prompt_regex: A regular expression that the input must match to be submitted.
        :returns: The user input.
        """
        self.ensure_unblocked()
        return self._show_prompt_input(prompt_text, prompt_regex)

    @abstractmethod
    def _show_prompt_input(self, prompt_text: str, prompt_regex: Regex | None) -> str:
        pass

    def show_prompt_password(self, prompt_text: str, prompt_regex: Regex | None = None) -> str:
        """
        Prompts the user for password input. Blocks until the user submits their input.\n
        Must not be called while the presenter is blocked.
        :param prompt_text: The prompt text to show.
        :param prompt_regex: A regular expression that the password must match to be submitted.
        :returns: The user password input.
        """
        self.ensure_unblocked()
        return self._show_prompt_password(prompt_text, prompt_regex)

    @abstractmethod
    def _show_prompt_password(self, prompt_text: str, prompt_regex: Regex | None) -> str:
        pass

    @abstractmethod
    def create_progress_bar(self) -> ProgressBar:
        """
        Creates a new progress bar.
        :returns: The new progress bar.
        """

    @abstractmethod
    def create_chooser(self) -> Chooser:
        """
        Creates a new chooser.
        :returns: The new chooser.
        """

    @abstractmethod
    def is_blocked(self) -> bool:
        """
        Retrieves whether this presenter is currently blocked.
        :return: Whether this presenter is blocked.
        """

    @abstractmethod
    def ensure_unblocked(self) -> None:
        """
        Ensures that this presenter is currently unblocked.
        Throws an error if it is blocked.
        """
