# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from time import sleep

from sbcc.features.demo import CATEGORY_SOFTWARE_UTILS
from sbcc_framework.feature import feature
from sbcc_framework.feature.utility import Utility
from sbcc_framework.presenter import Presenter


@feature(
    name="install-vpn",
    display_name="Install VPN",
    description="Convenience utility for layering VPN provider packages",
    category=CATEGORY_SOFTWARE_UTILS
)
class InstallVPN(Utility):
    providers: dict[str, str] = {"mullvad": "Mullvad VPN", "ivpn": "IVPN", "protonvpn": "Proton VPN"}

    def is_available(self) -> str | None:
        return None

    def run(self, presenter: Presenter) -> int | None:
        chooser = presenter.create_chooser()
        chooser.set_context("Choose a VPN provider")
        for key, value in self.providers.items():
            chooser.add_option(key, value)
        choice = chooser.choose()
        provider = self.providers[choice]

        progress_bar = presenter.create_progress_bar()
        progress_bar.set_context(f"Installing {provider}...")
        progress_bar.show()
        while progress_bar.get_progress() < 1:
            progress_bar.add_progress(0.1)
            sleep(0.5)
        progress_bar.set_pulse(True)
        progress_bar.set_context("Cleaning up")
        sleep(4)
        progress_bar.close()
        presenter.show_prompt_text(f"{provider} was installed successfully!")

        return 0
