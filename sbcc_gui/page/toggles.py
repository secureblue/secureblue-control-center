# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Thread
from typing import Any, Callable, Final
from gi.repository import GLib
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.toggle import Toggle
from sbcc_gui.page import FeaturesPage
from sbcc_gui.widget.row import ToggleRow
from util import gettext_marker

_: Final = gettext_marker()


class TogglesPage(FeaturesPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title(_("Toggles"))

    def add_toggle(self, compiled: CompiledFeature[Toggle], callback: Callable[[ToggleRow], Any]) -> None:
        category_name = compiled.category.name
        if category_name not in self.categories:
            self.insert_category(compiled.category)

        wrapper = ToggleRow(
            name=compiled.name,
            title=compiled.display_name,
            subtitle=compiled.description,
            callback=callback
        )

        Thread(name=f"sbcc_gui:{compiled.name}:set-initial-state", target=self.set_initial_state,
               args=(compiled, wrapper)).start()

        self.categories[category_name].add(wrapper.get_row())

    def set_initial_state(self, compiled: CompiledFeature[Toggle], wrapper: ToggleRow) -> None:
        def toggle_on(__capture: ToggleRow = wrapper) -> None:
            wrapper.block_handler()
            wrapper.get_row().set_active(True)
            wrapper.unblock_handler()

        def toggle_disable(reason: str, *, __capture: ToggleRow = wrapper) -> None:
            row = wrapper.get_row()
            row.set_tooltip_text(reason)
            row.set_activatable(False)
            row.set_sensitive(False)

        try:
            unavailable_context = compiled.feature.is_available()
            if unavailable_context is not None:
                GLib.idle_add(toggle_disable, unavailable_context)
                return

            if compiled.feature.get_state():
                GLib.idle_add(toggle_on)
        except Exception as e:
            self.main_window.show_error_and_exit(compiled, e)
