# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import importlib
import pkgutil

from pathlib import Path


def load_features() -> None:
    """
    Loads all available features into their respective registries.
    """
    for _, module_name, _ in pkgutil.walk_packages([str(Path(__file__).parent)], prefix=__name__ + "."):
        importlib.import_module(module_name)
