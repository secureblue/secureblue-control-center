# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from typing import Any, Callable, Final
from gi.repository import Gtk, Adw
from sbcc_framework.feature import BooleanResponse
from sbcc_util import gettext_marker

_: Final = gettext_marker()


class BaseDialog(Adw.AlertDialog):
    cancel_func: Callable[..., Any] | None
    had_response: bool = False

    def __init__(self, cancel_func: Callable[..., Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cancel_func = cancel_func

        self.connect("response", self._on_response_internal)

    @abstractmethod
    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        pass

    def _on_response_internal(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if not self.had_response and response_id == "close" and self.cancel_func is not None:
            self.cancel_func()
            return
        self.had_response = True
        self._on_response(dialog, response_id)


class TextDialog(BaseDialog):
    callback: Callable[..., Any] | None

    def __init__(self, callback: Callable[..., Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.add_response("ok", _("Ok"))
        self.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if self.callback is not None and response_id == "ok":
            self.callback()


class BooleanDialog(BaseDialog):
    callback: Callable[[bool], Any]

    def __init__(self, callback: Callable[[bool], Any], default: BooleanResponse = BooleanResponse.NONE,
                 suggested: BooleanResponse = BooleanResponse.NONE, destructive: BooleanResponse = BooleanResponse.NONE,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.add_response("no", _("No"))
        self.add_response("yes", _("Yes"))

        if default is not BooleanResponse.NONE:
            self.set_default_response("yes" if default is BooleanResponse.YES else "no")

        for response, appearance in [(suggested, Adw.ResponseAppearance.SUGGESTED),
                                     (destructive, Adw.ResponseAppearance.DESTRUCTIVE)]:
            if response is not BooleanResponse.NONE:
                self.set_response_appearance("yes" if response is BooleanResponse.YES else "no", appearance)

        self.set_prefer_wide_layout(True)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id in ["yes", "no"]:
            self.callback(response_id == "yes")


class InputDialog(BaseDialog):
    callback: Callable[[str], Any]
    entry_row: Adw.EntryRow

    def __init__(self, callback: Callable[[str], Any], entry_row: Adw.EntryRow | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.entry_row = Adw.EntryRow(title=_("Enter text")) if entry_row is None else entry_row
        group = Adw.PreferencesGroup()
        group.add(self.entry_row)
        self.set_extra_child(group)

        self.add_response("ok", _("Ok"))
        self.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

        self.entry_row.connect("entry-activated", self._on_activate)

    def focus_input(self) -> None:
        self.entry_row.grab_focus()

    # noinspection PyUnusedLocal
    def _on_activate(self, entry_row: Adw.EntryRow) -> None:
        self.emit("response", "ok")
        self.close()

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id == "ok":
            self.callback(self.entry_row.get_text())


class PasswordDialog(InputDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(entry_row=Adw.PasswordEntryRow(title=_("Enter password")), *args, **kwargs)


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
    callback: Callable[[str], Any]
    list_box: Gtk.ListBox
    options: dict[str, Adw.ButtonRow]

    def __init__(self, callback: Callable[[str], Any], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.set_extra_child(self.list_box)

        self.add_response("submit", _("Confirm"))
        self.set_response_appearance("submit", Adw.ResponseAppearance.SUGGESTED)

        self.options = dict()

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
        self.options[key] = row

    def remove_option(self, key: str) -> None:
        if key not in self.options:
            raise ValueError("No such key")
        self.list_box.remove(self.options[key])
        self.options.pop(key)

    def select_option(self, key: str) -> None:
        if key not in self.options:
            raise ValueError("No such key")
        self.list_box.select_row(self.options[key])

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if self.callback and response_id == "submit":
            self.callback(self.list_box.get_selected_row().get_name())


class FatalErrorDialog(BaseDialog):
    callback: Callable[..., Any] | None

    def __init__(self, callback: Callable[..., Any] | None = None):
        super().__init__(
            heading=_("Fatal Error"),
            body=_("A fatal error has occurred.\nSee logs for additional information.\n\nThe application will exit.")
        )

        self.callback = callback

        self.add_response("exit", _("Close Application"))
        self.set_response_appearance("exit", Adw.ResponseAppearance.DESTRUCTIVE)

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if self.callback is not None:
            self.callback()
