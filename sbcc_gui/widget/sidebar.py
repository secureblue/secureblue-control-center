# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Any, cast
from gi.repository import Adw


class SidebarEntry(Adw.SidebarItem):
    callback: Callable[[], Any]

    def __init__(self, *args, callback: Callable[[], Any], **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.callback = callback


class Sidebar(Adw.Bin):
    sidebar: Adw.Sidebar
    section: Adw.SidebarSection

    def __init__(self):
        super().__init__()

        self.sidebar = Adw.Sidebar()
        self.section = Adw.SidebarSection()
        self.callbacks = {}

        self.sidebar.append(self.section)

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(Adw.HeaderBar())
        toolbar_view.set_content(self.sidebar)

        self.sidebar.connect("activated", self._on_entry_selected)

        self.set_child(toolbar_view)

    def add_entry(self, label: str, icon_name: str, callback: Callable[[], Any]) -> None:
        """
        Adds an entry to the sidebar.
        :param label: The label of the entry to add.
        :param icon_name: The name of the icon to show in the new entry.
        :param callback: The callback to invoke when the entry is selected.
        """
        self.section.append(SidebarEntry(title=label, icon_name=icon_name, callback=callback))

    def _on_entry_selected(self, _: Adw.Sidebar, idx: int) -> None:
        entry = self.sidebar.get_item(idx)
        if entry is not None:
            cast(SidebarEntry, entry).callback()
