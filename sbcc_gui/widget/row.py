# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Final, Self
from util import gettext_marker
from gi.repository import Gtk, Adw

_: Final = gettext_marker()


class SidebarRow(Gtk.ListBoxRow):
    def __init__(self, name: str, label: str, icon_name: str):
        super().__init__(name=name, height_request=45)

        box = Gtk.Box(spacing=5)
        box.append(Gtk.Image(icon_name=icon_name))
        box.append(Gtk.Label(label=label, xalign=0))

        self.set_child(box)


class BlockableRow[T]:
    row: Adw.PreferencesRow
    callback: Callable[[Self], None]
    handler_id: int

    def __init__(self, row: T, signal_name: str, callback: Callable[[Self], None]):
        if not isinstance(row, Adw.PreferencesRow):
            raise TypeError("Row is not an Adw.PreferencesRow")

        self.row = row
        self.callback = callback
        self.handler_id = self.row.connect(signal_name, self._on_change)

    def get_row(self) -> T:
        return self.row

    def block_handler(self) -> None:
        self.row.handler_block(self.handler_id)

    def unblock_handler(self) -> None:
        self.row.handler_unblock(self.handler_id)

    # noinspection PyUnusedLocal
    def _on_change(self, *args) -> None:
        self.callback(self)


class ToggleRow(BlockableRow[Adw.SwitchRow]):
    def __init__(self, *args, callback: Callable[[Self], None], **kwargs):
        super().__init__(row=Adw.SwitchRow(*args, **kwargs), signal_name="notify::active", callback=callback)


class UtilityRow(BlockableRow[Adw.ActionRow]):
    def __init__(self, *args, callback: Callable[[Self], None], **kwargs):
        super().__init__(row=Adw.ActionRow(*args, **kwargs), signal_name="activated", callback=callback)

        button = Gtk.Button(
            label=_("Run"),
            css_classes=["suggested_action"],
            valign=Gtk.Align.CENTER
        )
        button.connect("clicked", lambda _args: self.get_row().emit("activated"))
        self.get_row().add_suffix(button)
        self.get_row().set_activatable(False)
