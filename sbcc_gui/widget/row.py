# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Final, Self, cast
from gi.repository import Gtk, Adw, GObject, Gio
from sbcc_util import gettext_marker

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


class PreferenceRow(BlockableRow[Adw.SwitchRow]):
    def __init__(self, *args, callback: Callable[[Self], None], **kwargs):
        super().__init__(row=Adw.SwitchRow(*args, **kwargs), signal_name="notify::active", callback=callback)


class MultiPreferenceRow(BlockableRow[Adw.ComboRow]):
    store: Gio.ListStore

    def __init__(self, *args, callback: Callable[[Self], None], **kwargs):
        super().__init__(row=Adw.ComboRow(*args, **kwargs), signal_name="notify::selected", callback=callback)

        # Block handler to avoid firing event during widget build
        self.block_handler()
        self.store = Gio.ListStore.new(MultiPreferenceRow.LabeledKey)
        self.get_row().set_model(self.store)
        self.get_row().set_expression(Gtk.PropertyExpression.new(MultiPreferenceRow.LabeledKey, None, "label"))

    def ready(self) -> None:
        self.unblock_handler()

    def add_option(self, key: str, value: str) -> None:
        self.store.append(MultiPreferenceRow.LabeledKey(key=key, label=value))

    def get_selected_option(self) -> str:
        return cast(MultiPreferenceRow.LabeledKey, self.get_row().get_selected_item()).key

    def set_selected_option(self, key: str) -> None:
        for i in range(self.store.get_n_items()):
            if cast(MultiPreferenceRow.LabeledKey, self.store.get_item(i)).key == key:
                self.get_row().set_selected(i)
                return
        raise ValueError(f"Row has no option with key {key}")

    class LabeledKey(GObject.Object):
        key = GObject.Property(type=str)
        label = GObject.Property(type=str)

        def __init__(self, key: str, label: str):
            super().__init__()

            self.key = key
            self.label = label


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
