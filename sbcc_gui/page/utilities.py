# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from threading import Thread
from typing import Any, Final
from gi.repository import GLib
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.utility import Utility
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
            name=compiled.name,
            title=compiled.display_name,
            subtitle=compiled.description,
            callback=callback
        )

        Thread(name=f"sbcc_gui:{compiled.name}:set-initial-state", target=self.set_initial_state,
               args=(compiled, wrapper)).start()

        self.categories[category_name].add(wrapper.get_row())

    def set_initial_state(self, compiled: CompiledFeature[Utility], wrapper: UtilityRow) -> None:
        def disable_utility(reason: str) -> None:
            row = wrapper.get_row()
            row.set_tooltip_text(_("This utility is not available: {0}").format(reason))
            row.set_activatable(False)
            row.set_sensitive(False)
            self.feature_loaded()

        try:
            unavailable_context = compiled.feature.is_available()
            if unavailable_context is not None:
                GLib.idle_add(disable_utility, unavailable_context)
            else:
                self.feature_loaded()
        except Exception as e:
            self.main_window.show_error_and_exit(compiled, e)
