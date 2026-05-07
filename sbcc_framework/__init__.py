# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

"""
The secureblue Control Center framework, providing a UI-agnostic, thread-safe API to interact with the user.
"""


class PresenterLock:
    """
    Holds the lock for blocking presenters.
    """

    __blocked: bool = False

    def is_blocked(self) -> bool:
        return self.__blocked

    def block(self) -> None:
        self.__blocked = True

    def unblock(self) -> None:
        self.__blocked = False

    def cancel(self):
        raise RuntimeError("Cancelling is not implemented for this presenter")
