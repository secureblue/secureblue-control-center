# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from sbcc.features.demo import CATEGORY_HARDENING_PREFS
from sbcc_framework.feature import feature, Environment
from sbcc_framework.feature.preference import Preference
from sbcc_framework.presenter import Presenter


@feature(
    name="xwayland-support",
    display_name="Xwayland support",
    description="Enables support for legacy X11 applications",
    category=CATEGORY_HARDENING_PREFS,
    environment=Environment.DESKTOP
)
class XWayland(Preference):
    def get_state(self) -> bool:
        return False

    def set_state(self, presenter: Presenter, state: bool) -> bool:
        if state:
            if presenter.show_prompt_boolean("Enabling Xwayland is a security degradation. Do you want to continue?"):
                presenter.show_text("Enabled Xwayland.")
            else:
                presenter.show_text("Aborted.")
                return False
        return state
