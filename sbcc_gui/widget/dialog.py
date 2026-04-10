# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from typing import Any, Callable, Final
from gi.repository import Gtk, Adw
from util import gettext_marker

_: Final = gettext_marker()


class BaseDialog(Adw.AlertDialog):
    cancel_func: Callable[..., Any] | None

    def __init__(self, cancel_func: Callable[..., Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cancel_func = cancel_func

        self.connect("response", self._on_response_internal)

    @abstractmethod
    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        pass

    def _on_response_internal(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id == "close" and self.cancel_func:
            self.cancel_func()
            return
        self._on_response(dialog, response_id)


class TextDialog(BaseDialog):
    callback: Callable[..., Any] | None

    def __init__(self, callback: Callable[..., Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.add_response("ok", _("Ok"))
        self.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id == "ok":
            self.callback()


class BooleanDialog(BaseDialog):
    callback: Callable[[bool], Any] | None

    def __init__(self, callback: Callable[[bool], Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.add_response("no", _("No"))
        # self.set_response_appearance("no", Adw.ResponseAppearance.DESTRUCTIVE)

        self.add_response("yes", _("Yes"))
        # self.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)

        self.set_prefer_wide_layout(True)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id in ["yes", "no"]:
            self.callback(response_id == "yes")


class InputDialog(BaseDialog):
    callback: Callable[[str], Any] | None
    entry_row: Adw.EntryRow

    def __init__(self, callback: Callable[[str], Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.entry_row = Adw.EntryRow(title=_("Enter text"))
        group = Adw.PreferencesGroup()
        group.add(self.entry_row)
        self.set_extra_child(group)

        self.add_response("ok", _("Ok"))
        self.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id == "ok":
            self.callback(self.entry_row.get_text())


class PasswordDialog(BaseDialog):
    callback: Callable[[str], Any] | None
    entry_row: Adw.PasswordEntryRow

    def __init__(self, callback: Callable[[str], Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.entry_row = Adw.PasswordEntryRow(title=_("Enter password"))
        group = Adw.PreferencesGroup()
        group.add(self.entry_row)
        self.set_extra_child(group)

        self.add_response("ok", _("Ok"))
        self.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id == "ok":
            self.callback(self.entry_row.get_text())


class ProgressDialog(BaseDialog):
    progress_bar: Gtk.ProgressBar

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.progress_bar = Gtk.ProgressBar()
        group = Adw.PreferencesGroup()
        group.add(self.progress_bar)
        self.set_extra_child(group)

        self.set_can_close(False)

    def close(self) -> None:
        self.force_close()

    def get_progress_bar(self) -> Gtk.ProgressBar:
        return self.progress_bar

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        pass


class ChooserDialog(BaseDialog):
    callback: Callable[[str], Any] | None = None
    list_box: Gtk.ListBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.set_extra_child(self.list_box)

        self.add_response("submit", _("Confirm"))
        self.set_response_appearance("submit", Adw.ResponseAppearance.SUGGESTED)

    def choose_callback(self, parent: Adw.ApplicationWindow, callback: Callable[[str], Any],
                        cancel_func: Callable[..., Any]):
        self.callback = callback
        self.cancel_func = cancel_func
        self.choose(parent)

    def add_option(self, key: str, value: str) -> None:
        row = Adw.ButtonRow(
                name=key,
                child=Gtk.Label(
                    label=value,
                    xalign=0,
                    margin_start=8,
                    margin_top=5,
                    margin_end=5,
                    margin_bottom=5
                )
            )
        self.list_box.append(row)
        if self.list_box.get_selected_row() is None:
            self.list_box.select_row(row)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if self.callback and response_id == "submit":
            self.callback(self.list_box.get_selected_row().get_name())


class FatalErrorDialog(BaseDialog):
    callback: Callable[..., Any] | None

    def __init__(self, callback: Callable[..., Any] = None):
        super().__init__(
            heading=_("Fatal Error"),
            body=_("A fatal error has occurred.\nSee logs for additional information.\n\nThe application will exit.")
        )

        self.callback = callback

        self.add_response("exit", _("Close Application"))
        self.set_response_appearance("exit", Adw.ResponseAppearance.DESTRUCTIVE)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        self.callback()
