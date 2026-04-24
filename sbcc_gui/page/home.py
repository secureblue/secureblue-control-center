# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Final
from gi.repository import Adw
from util import gettext_marker

_: Final = gettext_marker()


class HomePage(Adw.Bin):
    def __init__(self):
        super().__init__()
        self.set_child(Adw.StatusPage(
            title="secureblue Control Center",
            description=_("Home"),
            icon_name="go-home-symbolic"
        ))
