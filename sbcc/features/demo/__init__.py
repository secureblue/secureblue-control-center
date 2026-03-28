# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from sbcc_framework.feature import Category

CATEGORY_SOFTWARE = Category(
    name="software",
    display_name="Additional software",
    description="Utilities for additional software installation and management",
    priority=1
)

CATEGORY_HARDENING_TOGGLES = Category(
    name="hardening",
    display_name="Hardening",
    description="Toggles to disable various hardening features for compatibility",
    priority=5
)
