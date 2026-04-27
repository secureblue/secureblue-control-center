# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Thread
from typing import Any, Callable, Final
from gi.repository import GLib
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.preference import Preference
from sbcc_gui.page import FeaturesPage
from sbcc_gui.widget.row import PreferenceRow
from util import gettext_marker

_: Final = gettext_marker()


class PreferencesPage(FeaturesPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title(_("Preferences"))

    def add_preference(self, compiled: CompiledFeature[Preference], callback: Callable[[PreferenceRow], Any]) -> None:
        category_name = compiled.category.name
        if category_name not in self.categories:
            self.insert_category(compiled.category)

        wrapper = PreferenceRow(
            name=compiled.name,
            title=compiled.display_name,
            subtitle=compiled.description,
            callback=callback
        )

        Thread(name=f"sbcc_gui:{compiled.name}:set-initial-state", target=self.set_initial_state,
               args=(compiled, wrapper)).start()

        self.categories[category_name].add(wrapper.get_row())

    def set_initial_state(self, compiled: CompiledFeature[Preference], wrapper: PreferenceRow) -> None:
        def toggle_on(__capture: PreferenceRow = wrapper) -> None:
            wrapper.block_handler()
            wrapper.get_row().set_active(True)
            wrapper.unblock_handler()

        def disable_preference(reason: str, *, __capture: PreferenceRow = wrapper) -> None:
            row = wrapper.get_row()
            row.set_tooltip_text(reason)
            row.set_activatable(False)
            row.set_sensitive(False)

        try:
            unavailable_context = compiled.feature.is_available()
            if unavailable_context is not None:
                GLib.idle_add(disable_preference, unavailable_context)
                return

            if compiled.feature.get_state():
                GLib.idle_add(toggle_on)
        except Exception as e:
            self.main_window.show_error_and_exit(compiled, e)
