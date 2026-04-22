# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import dataclasses

from abc import ABC
from enum import Enum, auto
from typing import Callable, Final, List
from util import gettext_marker, has_gui

_: Final = gettext_marker()


class Frontend(Enum):
    """
    Which frontend this feature supports. (e.g. for CLI-only features)
    """
    CLI = auto()
    """Indicates support only for CLI frontend."""
    GUI = auto()
    """Indicates support only for GUI frontend."""
    ANY = auto()
    """Indicates support for both CLI and GUI frontends."""


class Environment(Enum):
    """
    Which environment this feature supports. (e.g. for server-only features)
    """
    SERVER = auto()
    """Indicates support only for server environment."""
    DESKTOP = auto()
    """Indicates support only for desktop environment."""
    ANY = auto()
    """Indicates support for both server and desktop environments."""


@dataclasses.dataclass
class Category:
    """
    A feature category, used for grouping and additional information in the UI.
    """

    name: str
    """The name of this category."""
    display_name: str
    """The display name of this category."""
    description: str
    """The description of this category."""
    priority: int = 0
    """The priority of this category. Higher number means higher priority."""


DEFAULT_CATEGORY: Final = Category(
    name="other",
    display_name=_("Uncategorized"),
    description=_("Uncategorized features"),
    priority=-1
)
"""The global default category."""


@dataclasses.dataclass
class Feature(ABC):
    """
    Abstract base class for all features.
    """

    # noinspection PyMethodMayBeStatic
    def is_available(self) -> str | None:
        """
        Invoked to check if this feature is available. If the feature is unavailable it cannot be used.
        :returns: None if feature is available,
          otherwise a string that provides additional context why this feature is unavailable.
        """
        return None


@dataclasses.dataclass
class CompiledFeature[T]:
    """
    A feature with metadata.
    """

    name: str
    display_name: str
    description: str
    category: Category
    frontend: Frontend
    environment: Environment
    feature: T

    def supports_cli(self) -> bool:
        """
        Retrieves whether this feature supports CLI frontend.
        :return: Whether this feature supports CLI frontend.
        """
        return self.frontend == Frontend.ANY or self.frontend == Frontend.CLI

    def supports_gui(self) -> bool:
        """
        Retrieves whether this feature supports GUI frontend.
        :return: Whether this feature supports GUI frontend.
        """
        return self.frontend == Frontend.ANY or self.frontend == Frontend.GUI

    def supports_server(self) -> bool:
        """
        Retrieves whether this feature supports server environment.
        :return: Whether this feature supports server environment.
        """
        return self.environment == Environment.ANY or self.environment == Environment.SERVER

    def supports_desktop(self) -> bool:
        """
        Retrieves whether this feature supports desktop environment.
        :return: Whether this feature supports desktop environment.
        """
        return self.environment == Environment.ANY or self.environment == Environment.DESKTOP

    def supports_environment(self) -> bool:
        """
        Retrieves whether this feature supports the current environment.
        :return: Whether this feature supports the current environment.
        """
        if has_gui():
            return self.supports_desktop()
        else:
            return self.supports_server()


def feature(
        name: str, display_name: str, description: str, category: Category = DEFAULT_CATEGORY,
        frontend: Frontend = Frontend.ANY, environment: Environment = Environment.ANY
) -> Callable[[type[Feature]], type[Feature]]:
    """
    Compiles and registers a feature with metadata.
    :param name: The name of the feature.
    :param display_name: The display name of the feature.
    :param description: The description of the feature.
    :param category: The category of the feature.
    :param frontend: Which UI frontends this feature supports.
    :param environment: Which environments this feature supports.
    """

    def _compile(_feature: type[Feature]) -> type[Feature]:
        if not issubclass(_feature, Feature):
            raise TypeError("Feature {name} must inherit from class Feature")

        compiled = CompiledFeature(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            frontend=frontend,
            environment=environment,
            feature=_feature()
        )

        cls = compiled.feature.__class__.__mro__[1]
        registry: List[CompiledFeature] = getattr(cls, "REGISTRY", None)
        if registry is None:
            raise AttributeError(f"Feature class '{cls.__name__}' has no registry")
        registry.append(compiled)

        return _feature
    return _compile
