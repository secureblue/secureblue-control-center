# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Any, Final, cast, override
from gi.repository import Gtk, Adw
from sbcc_framework import Regex
from sbcc_framework.feature import BooleanResponse
from sbcc_util import gettext_marker, require_not_none

_: Final[Callable[[str], str]] = gettext_marker()


class BaseDialog(Adw.AlertDialog):
    cancel_func: Callable[[], Any] | None
    had_response: bool = False

    def __init__(self, cancel_func: Callable[[], Any] | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cancel_func = cancel_func

        self.connect("response", self._on_response_internal)

        self.add_css_class("view")

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        raise NotImplementedError

    def _on_response_internal(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if self.cancel_func is not None and response_id == "close" and not self.had_response:
            self.cancel_func()
            return
        self.had_response = True
        self._on_response(dialog, response_id)


class TextDialog(BaseDialog):
    callback: Callable[[], Any] | None

    def __init__(self, callback: Callable[[], Any] | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.add_response("ok", _("Ok"))
        self.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

    @override
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

    @override
    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id in ["yes", "no"]:
            self.callback(response_id == "yes")


class InputDialog(Adw.Dialog):
    callback: Callable[[str], Any]
    entry_row: Adw.EntryRow
    regex: Regex | None
    cancel_func: Callable[..., Any] | None
    popover: Gtk.Popover
    had_response: bool = False
    input_invalid: bool = False

    def __init__(self, heading: str, body: str, callback: Callable[[str], Any], entry_row: Adw.EntryRow | None = None,
                 regex: Regex | None = None, cancel_func: Callable[..., Any] | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs, width_request=350)

        self.callback = callback
        self.entry_row = Adw.EntryRow(title=_("Enter text")) if entry_row is None else entry_row
        self.regex = regex
        self.cancel_func = cancel_func

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_top=30, margin_bottom=30, margin_start=30, margin_end=30
        )

        box.append(
            Gtk.Label(
                label=heading,
                css_classes=["heading", "title-3"],
                margin_bottom=10
            )
        )
        box.append(
            Gtk.Label(label=body, margin_bottom=20)
        )

        group = Adw.PreferencesGroup(margin_bottom=28)
        group.add(self.entry_row)
        box.append(group)

        button = Gtk.Button(label=_("Submit"), css_classes=["suggested-action"])
        button.connect("clicked", self._on_submit)
        box.append(button)

        self.set_child(box)

        if regex is not None and regex.has_context():
            popover_text = _("Invalid input: {0}").format(regex.get_context())
        else:
            popover_text = _("Input does not match required pattern.")

        self.popover = Gtk.Popover(
            position=Gtk.PositionType.BOTTOM,
            autohide=False
        )
        self.popover.set_parent(self.entry_row)
        self.popover.set_child(
            Gtk.Label(
                label=popover_text,
                css_classes=["error"],
                margin_top=5, margin_bottom=5, margin_start=5, margin_end=5
            )
        )

        self.connect("realize", self._on_realize)
        self.connect("closed", self._on_close)

        self.entry_row.connect("entry-activated", self._on_activate)
        self.entry_row.connect("changed", self._on_input_changed)

        click_controller = Gtk.GestureSingle(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        click_controller.connect("begin", self._on_focus_changed)
        self.add_controller(click_controller)

        self.add_css_class("view")

    def focus_input(self) -> None:
        self.entry_row.grab_focus_without_selecting()

    def _on_realize(self, *_) -> None:
        window = require_not_none(self.get_root())
        focus_handler = window.connect("notify::is-active", self._on_focus_changed)
        self.connect("unrealize", lambda *_: window.disconnect(focus_handler))

    def _on_focus_changed(self, *_) -> None:
        if self.popover.is_visible():
            self.popover.popdown()

    def _on_activate(self, *_) -> None:
        self._on_submit()

    def _on_input_changed(self, *_) -> None:
        if self.input_invalid:
            self.input_invalid = False
            self.entry_row.remove_css_class("error")
            self.popover.popdown()

    @override
    def _on_submit(self, *_) -> None:
        text = self.entry_row.get_text()

        if self.regex is not None and not self.regex.match(text):
            self.input_invalid = True
            self.entry_row.add_css_class("error")
            self.popover.popup()
            return

        self.had_response = True

        self.close()
        self.callback(text)

    def _on_close(self, *_) -> None:
        if not self.had_response and self.cancel_func is not None:
            self.cancel_func()


class PasswordDialog(InputDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, entry_row=Adw.PasswordEntryRow(title=_("Enter password")))


class ProgressDialog(BaseDialog):
    progress_bar: Gtk.ProgressBar
    body: Gtk.Label

    def __init__(self, body: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.progress_bar = Gtk.ProgressBar()
        self.body = Gtk.Label(margin_bottom=30)

        group = Adw.PreferencesGroup()
        group.add(self.progress_bar)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(self.body)
        box.append(group)

        self.set_extra_child(box)

        if body is not None:
            self.set_body(body)

        self.set_can_close(False)

    @override
    def set_body(self, body: str) -> None:
        self.body.set_text(body)

    @override
    def close(self) -> None:
        self.force_close()

    def get_progress_bar(self) -> Gtk.ProgressBar:
        return self.progress_bar

    def set_show_percentage(self, value: bool) -> None:
        self.progress_bar.set_show_text(value)

        # Dynamically adjust for additional space occupied by
        # the percentage being shown above the progress bar.
        if value:
            self.body.set_margin_bottom(14)
        else:
            self.body.set_margin_bottom(30)

    @override
    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        pass


class ChooserDialog(BaseDialog):
    callback: Callable[[str], Any]
    list_box: Gtk.ListBox
    options: dict[str, Adw.ButtonRow]

    def __init__(self, callback: Callable[[str], Any], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, css_classes=["boxed-list"])
        self.set_extra_child(self.list_box)

        self.add_response("submit", _("Confirm"))
        self.set_response_appearance("submit", Adw.ResponseAppearance.SUGGESTED)

        self.options = {}

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
        row.connect("activate", self._on_activate)

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

    # noinspection PyUnusedLocal
    def _on_activate(self, row: Adw.ButtonRow) -> None:
        self.emit("response", "submit")
        self.close()

    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if self.callback and response_id == "submit":
            self.callback(require_not_none(self.list_box.get_selected_row()).get_name())


class FatalErrorDialog(BaseDialog):
    callback: Callable[[], Any] | None

    def __init__(self, callback: Callable[[], Any] | None = None):
        super().__init__(
            heading=_("Fatal Error"),
            body=_("A fatal error has occurred.\nSee logs for additional information.\n\nThe application will exit.")
        )

        self.callback = callback

        self.add_response("exit", _("Close Application"))
        self.set_response_appearance("exit", Adw.ResponseAppearance.DESTRUCTIVE)

    @override
    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if self.callback is not None:
            self.callback()
