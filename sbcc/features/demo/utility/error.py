# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import override
from sbcc_framework.feature import feature, Frontend
from sbcc_framework.feature.utility import Utility
from sbcc_framework.presenter import Presenter


@feature(
    name="error",
    display_name="Error Utility",
    description="Will throw an exception in the feature script, demonstrating error handling",
    frontend=Frontend.GUI
)
class ErrorUtil(Utility):
    @override
    def run(self, presenter: Presenter) -> None:
        raise RuntimeError
