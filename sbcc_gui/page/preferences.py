# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Thread
from typing import Any, Callable, Final
from gi.repository import GLib
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.preference import Preference, MultiPreference
from sbcc_gui.page import FeaturesPage
from sbcc_gui.widget.row import PreferenceRow, MultiPreferenceRow
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

        def set_initial_state(_compiled: CompiledFeature[Preference], _wrapper: PreferenceRow) -> None:
            def toggle_on() -> None:
                _wrapper.block_handler()
                _wrapper.get_row().set_active(True)
                _wrapper.unblock_handler()

            def disable_preference(reason: str) -> None:
                row = _wrapper.get_row()
                row.set_tooltip_text(reason)
                row.set_activatable(False)
                row.set_sensitive(False)

            try:
                unavailable_context = _compiled.feature.is_available()
                if unavailable_context is not None:
                    GLib.idle_add(disable_preference, unavailable_context)
                    return

                if _compiled.feature.get_state():
                    GLib.idle_add(toggle_on)
            except Exception as e:
                self.main_window.show_error_and_exit(_compiled, e)

        Thread(name=f"sbcc_gui:{compiled.name}:set-initial-state", target=set_initial_state,
               args=(compiled, wrapper)).start()

        self.categories[category_name].add(wrapper.get_row())

    def add_multi_preference(self, compiled: CompiledFeature[MultiPreference],
                             callback: Callable[[MultiPreferenceRow], Any]) -> None:
        category_name = compiled.category.name
        if category_name not in self.categories:
            self.insert_category(compiled.category)

        wrapper = MultiPreferenceRow(
            name=compiled.name,
            title=compiled.display_name,
            subtitle=compiled.description,
            callback=callback
        )

        def set_initial_state(_compiled: CompiledFeature[MultiPreference], _wrapper: MultiPreferenceRow) -> None:
            def initialize(_options: dict[str, str], _state: str) -> None:
                for key, value in _options.items():
                    wrapper.add_option(key, value)
                _wrapper.set_selected_option(_state)
                _wrapper.ready()

            def disable_preference(reason: str) -> None:
                row = _wrapper.get_row()
                row.set_tooltip_text(reason)
                row.set_activatable(False)
                row.set_sensitive(False)

            try:
                unavailable_context = _compiled.feature.is_available()
                if unavailable_context is not None:
                    GLib.idle_add(disable_preference, unavailable_context)
                    return

                options = _compiled.feature.get_options()
                state = _compiled.feature.get_state()
                GLib.idle_add(initialize, options, state)
            except Exception as e:
                self.main_window.show_error_and_exit(_compiled, e)

        Thread(name=f"sbcc_gui:{compiled.name}:set-initial-state", target=set_initial_state,
               args=(compiled, wrapper)).start()

        self.categories[category_name].add(wrapper.get_row())
