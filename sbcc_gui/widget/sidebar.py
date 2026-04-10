# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Callable
from gi.repository import Adw, Gtk


class Sidebar(Adw.Bin):
    sidebar: Gtk.ListBox
    callbacks: dict[str, Callable[..., Any]] = dict()

    def __init__(self):
        super().__init__()

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(Adw.HeaderBar())

        self.sidebar = Gtk.ListBox(css_classes=["navigation-sidebar"])
        toolbar_view.set_content(Gtk.ScrolledWindow(child=self.sidebar))

        self.sidebar.connect("row-activated", self._on_row_activated)

        self.set_child(toolbar_view)

    def add_entry(self, entry: Gtk.ListBoxRow, callback: Callable[..., Any]) -> None:
        """
        Adds an entry to the sidebar.
        :param entry: The entry to add.
        :param callback: The callback to invoke when the row is selected.
        """
        if entry.get_name() == "GtkListBoxRow":
            raise ValueError("Entry must have a unique name")
        self.callbacks[entry.get_name()] = callback
        self.sidebar.append(entry)

    # noinspection PyUnusedLocal
    def _on_row_activated(self, listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        name = row.get_name()
        if name in self.callbacks:
            self.callbacks.get(name)()
