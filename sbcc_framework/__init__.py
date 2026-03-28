# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The secureblue Control Center framework, providing a UI-agnostic, thread-safe API to interact with the user.
"""

from abc import ABC, abstractmethod


class PresenterInterface(ABC):
    """
    Utility class to avoid circular dependencies.
    """

    _blocked: bool = False

    def is_blocked(self) -> bool:
        return self._blocked

    def block(self) -> None:
        self._blocked = True

    def unblock(self) -> None:
        self._blocked = False

    @abstractmethod
    def cancel(self):
        pass
