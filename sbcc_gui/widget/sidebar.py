# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Any
from gi.repository import Adw, Gtk


class Sidebar(Adw.Bin):
    sidebar: Gtk.ListBox
    callbacks: dict[str, Callable[[], Any]]

    def __init__(self):
        super().__init__()

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(Adw.HeaderBar())

        self.sidebar = Gtk.ListBox(css_classes=["navigation-sidebar"])
        toolbar_view.set_content(Gtk.ScrolledWindow(child=self.sidebar))

        self.sidebar.connect("row-activated", self._on_row_activated)

        self.set_child(toolbar_view)

        self.callbacks = {}

    def add_entry(self, entry: Gtk.ListBoxRow, callback: Callable[[], Any]) -> None:
        """
        Adds an entry to the sidebar.
        :param entry: The entry to add.
        :param callback: The callback to invoke when the row is selected.
        """
        if entry.get_name() == "GtkListBoxRow":
            msg = "Entry must have a unique name"
            raise ValueError(msg)
        self.callbacks[entry.get_name()] = callback
        self.sidebar.append(entry)

    def _on_row_activated(self, _: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        name = row.get_name()
        if name in self.callbacks:
            self.callbacks.get(name)()
