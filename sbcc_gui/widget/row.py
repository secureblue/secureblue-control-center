# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Final, Self, cast, Any
from gi.repository import Gtk, Adw, GObject, Gio
from sbcc_framework.feature import CompiledFeature
from sbcc_gui import on_gtk_thread
from sbcc_gui.page import FeaturesPage
from sbcc_gui.widget.dialog import ErrorDialog
from sbcc_util import gettext_marker, require_not_none

_: Final[Callable[[str], str]] = gettext_marker()


class SidebarRow(Gtk.ListBoxRow):
    def __init__(self, name: str, label: str, icon_name: str):
        super().__init__(name=name, height_request=45)

        box = Gtk.Box(spacing=5)
        box.append(Gtk.Image(icon_name=icon_name))
        box.append(Gtk.Label(label=label, xalign=0))

        self.set_child(box)


class FeatureRow[T: Adw.ActionRow]:
    row: T
    compiled: CompiledFeature
    page: FeaturesPage
    callback: Callable[[Self], None]
    handler_id: int
    handler_blocked: bool = False

    def __init__(self, row: T, compiled: CompiledFeature, page: FeaturesPage, callback: Callable[[Self], None],
                 signal_name: str):
        self.row = row
        self.compiled = compiled
        self.page = page
        self.callback = callback
        self.handler_id = self.row.connect(signal_name, self._on_change)

        self.row.set_name(compiled.name)
        self.row.set_title(compiled.display_name)
        self.row.set_subtitle(compiled.description)

    def get_row(self) -> T:
        return self.row

    def block_handler(self) -> None:
        if not self.handler_blocked:
            self.handler_blocked = True
            self.row.handler_block(self.handler_id)

    def unblock_handler(self) -> None:
        if self.handler_blocked:
            self.handler_blocked = False
            self.row.handler_unblock(self.handler_id)

    def _on_change(self, *_: Any) -> None:
        self.callback(self)

    @on_gtk_thread()
    def disable_with_error(self, error: Exception, aborted: bool) -> None:
        def show_error_dialog(*__) -> None:
            dialog = ErrorDialog(
                heading=_("Fatal error"),
                body=(_('The feature "{0}" has been{1} disabled due to an unexpected fatal error.')
                      + " "
                      + _("An application restart is necessary to attempt to restore functionality of the feature.")
                      + "\n\n"
                      + _("If the issue persists, please file a bug report with error details attached "
                          "via the button below."))
                .format(self.compiled.display_name, " " + _("aborted and") if aborted else ""),
                error=error,
                button_label=_("Acknowledge"), destructive=True
            )
            dialog.present(self.page.main_window.get_window())

        action_row = ErrorRow(
            compiled=self.compiled,
            page=self.page,
            callback=show_error_dialog
        )

        self.page.categories[self.compiled.category.name].replace(self.row, action_row.get_row())

        if aborted:
            show_error_dialog()


class PreferenceRow(FeatureRow[Adw.SwitchRow]):
    def __init__(self, compiled: CompiledFeature, page: FeaturesPage, callback: Callable[[Self], None]):
        super().__init__(row=Adw.SwitchRow(), compiled=compiled, page=page, callback=callback,
                         signal_name="notify::active")


class MultiPreferenceRow(FeatureRow[Adw.ComboRow]):
    store: Gio.ListStore["MultiPreferenceRow.LabeledKey"]

    def __init__(self, compiled: CompiledFeature, page: FeaturesPage, callback: Callable[[Self], None]):
        super().__init__(row=Adw.ComboRow(), compiled=compiled, page=page, callback=callback,
                         signal_name="notify::selected")

        # Block handler to avoid firing during widget build
        self.block_handler()
        self.store = Gio.ListStore.new(MultiPreferenceRow.LabeledKey)
        self.get_row().set_model(self.store)
        self.get_row().set_expression(Gtk.PropertyExpression.new(MultiPreferenceRow.LabeledKey, None, "label"))

    def add_option(self, key: str, value: str) -> None:
        self.store.append(MultiPreferenceRow.LabeledKey(key=key, label=value))

    def get_selected_option(self) -> str:
        return cast(MultiPreferenceRow.LabeledKey, self.get_row().get_selected_item()).key

    def set_selected_option(self, key: str) -> None:
        for i in range(self.store.get_n_items()):
            if require_not_none(self.store.get_item(i)).key == key:
                self.get_row().set_selected(i)
                return
        msg = f"Row has no option with key {key}"
        raise ValueError(msg)

    class LabeledKey(GObject.Object):
        key = GObject.Property(type=str)
        label = GObject.Property(type=str)

        def __init__(self, key: str, label: str):
            super().__init__()

            self.key = key
            self.label = label


class UtilityRow(FeatureRow[Adw.ActionRow]):
    def __init__(self, compiled: CompiledFeature, page: FeaturesPage, callback: Callable[[Self], None]):
        super().__init__(row=Adw.ActionRow(focusable=False), compiled=compiled, page=page, callback=callback,
                         signal_name="activated")

        button = Gtk.Button(
            label=_("Run"),
            valign=Gtk.Align.CENTER
        )
        button.add_css_class("accent")
        button.connect("clicked", lambda *_: self.get_row().emit("activated"))

        self.get_row().add_suffix(button)


class ErrorRow(FeatureRow[Adw.ActionRow]):
    def __init__(self, compiled: CompiledFeature, page: FeaturesPage, callback: Callable[[Self], None]):
        super().__init__(row=Adw.ActionRow(focusable=False), compiled=compiled, page=page, callback=callback,
                         signal_name="activated")

        button = Gtk.Button(
            child=Gtk.Image(icon_name="dialog-warning", icon_size=Gtk.IconSize.LARGE),
            valign=Gtk.Align.CENTER,
            tooltip_text=_("More information")
        )
        button.add_css_class("flat")
        button.add_css_class("destructive-action")
        button.connect("clicked", lambda *_: self.get_row().emit("activated"))

        self.get_row().add_suffix(button)
