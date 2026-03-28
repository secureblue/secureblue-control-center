# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from sbcc.features.demo import CATEGORY_HARDENING_TOGGLES
from sbcc_framework.feature import feature, Environment
from sbcc_framework.feature.toggle import Toggle
from sbcc_framework.presenter import Presenter


@feature(
    name="anticheat-support",
    display_name="Anticheat support",
    description="Enables ptrace, which is required by some anti-cheats",
    category=CATEGORY_HARDENING_TOGGLES,
    environment=Environment.DESKTOP
)
class AnticheatSupport(Toggle):
    def get_state(self) -> bool:
        return False

    def set_state(self, presenter: Presenter, state: bool) -> bool:
        if state:
            if presenter.show_prompt_boolean("Enabling ptrace is a security degradation. Do you want to continue?"):
                presenter.show_prompt_text("Enabled ptrace. Reboot to take effect.")
            else:
                presenter.show_text("Aborted.")
                return False
        else:
            presenter.show_prompt_text("Disabled ptrace. Reboot to take effect.")
        return state
