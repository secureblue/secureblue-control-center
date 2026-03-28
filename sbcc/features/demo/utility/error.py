# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from sbcc_framework.feature import feature, UI
from sbcc_framework.feature.utility import Utility
from sbcc_framework.presenter import Presenter


@feature(
    name="error",
    display_name="Error Utility",
    description="Will throw an exception in the feature script, demonstrating error handling",
    supports=UI.GUI
)
class ErrorUtil(Utility):
    def run(self, presenter: Presenter) -> int | None:
        raise RuntimeError("Error")
