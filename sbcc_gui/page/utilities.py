# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from threading import Thread
from typing import Any, Final
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.utility import Utility
from sbcc_gui import FeatureException, on_gtk_thread
from sbcc_gui.page import FeaturesPage
from sbcc_gui.widget.row import UtilityRow
from sbcc_util import gettext_marker

_: Final[Callable[[str], str]] = gettext_marker()


class UtilitiesPage(FeaturesPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, title=_("Utilities"))

    def add_utility(self, compiled: CompiledFeature[Utility], callback: Callable[[UtilityRow], Any]) -> None:
        self.feature_loading()

        category_name = compiled.category.name
        if category_name not in self.categories:
            self.insert_category(compiled.category)

        wrapper = UtilityRow(
            compiled=compiled,
            page=self,
            callback=callback
        )

        Thread(name=f"sbcc_gui:{compiled.name}:initialize", target=self.initialize_utility,
               args=(compiled, wrapper)).start()

        self.categories[category_name].add(wrapper.get_row())

    def initialize_utility(self, compiled: CompiledFeature[Utility], wrapper: UtilityRow) -> None:
        @on_gtk_thread()
        def disable_utility(reason: str) -> None:
            row = wrapper.get_row()
            row.set_tooltip_text(_("This utility is not available: {0}").format(reason))
            row.set_sensitive(False)

            self.feature_loaded()

        try:
            unavailable_context = compiled.feature.is_available()
            if unavailable_context is not None:
                disable_utility(unavailable_context)
            else:
                self.feature_loaded()
        except Exception as e:
            ex = FeatureException(f"Failed to initialize feature {compiled}")
            wrapper.disable_with_error(ex, False)
            self.feature_load_error(compiled, ex)
            raise ex from e
