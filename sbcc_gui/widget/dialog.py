# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Any, Final, cast, override
from gi.repository import Gtk, Adw, Gio
from sbcc_framework import Regex
from sbcc_framework.feature import BooleanResponse
from sbcc_gui.widget import ErrorDetails
from sbcc_util import gettext_marker, require_not_none, SBCC_ISSUES_PAGE

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


class ValidationDialog(Adw.Dialog):
    buttons: dict[str, tuple[str, str | None]]
    cancel_func: Callable[[], Any] | None
    had_response: bool = False

    def __init__(self, heading: str, body: str, child: Gtk.Widget,
                 buttons: dict[str, tuple[str, str | None]] | None = None,
                 cancel_func: Callable[[], Any] | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs, width_request=350, follows_content_size=True)

        self.buttons = buttons if buttons is not None else {"submit": (_("Submit"), "suggested-action")}
        self.cancel_func = cancel_func

        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        inner_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_top=30, margin_start=30, margin_end=30, margin_bottom=10,
            vexpand=True
        )

        inner_box.append(
            Gtk.Label(
                label=heading,
                css_classes=["heading", "title-3"],
                margin_bottom=10,
                halign=Gtk.Align.CENTER,
                justify=Gtk.Justification.CENTER
            )
        )
        inner_box.append(
            Gtk.Label(
                label=body,
                margin_bottom=20,
                halign=Gtk.Align.CENTER,
                justify=Gtk.Justification.CENTER,
                wrap=True
            )
        )

        inner_box.append(child)

        scrolled_window = Gtk.ScrolledWindow(
            child=inner_box,
            vexpand=True,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            propagate_natural_height=True
        )
        scrolled_window.add_css_class("undershoot-bottom")
        outer_box.append(scrolled_window)

        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True, spacing=10,
                             margin_top=10, margin_start=30, margin_end=30, margin_bottom=30)
        for response_id, (label, css_class) in self.buttons.items():
            button = Gtk.Button(child=Gtk.Label(
                label=label,
                margin_top=6,
                margin_start=10,
                margin_end=10,
                margin_bottom=6
            ))
            if css_class is not None:
                button.add_css_class(css_class)
            button.connect("clicked", lambda *_, __response_id=response_id: self._on_response(__response_id))
            button_box.append(button)
        outer_box.append(button_box)

        self.set_child(outer_box)

        self.connect("closed", self._on_close)

        self.add_css_class("view")
        self.set_presentation_mode(Adw.DialogPresentationMode.FLOATING)

    def _on_response(self, response_id: str) -> None:
        raise NotImplementedError

    def _on_close(self, *_: Any) -> None:
        if self.cancel_func is not None and not self.had_response:
            self.cancel_func()


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


class InputDialog(ValidationDialog):
    callback: Callable[[str], Any]
    entry_row: Adw.EntryRow
    regex: Regex | None
    popover: Gtk.Popover
    input_invalid: bool = False

    def __init__(self, callback: Callable[[str], Any], entry_row: Adw.EntryRow | None = None,
                 regex: Regex | None = None, *args, **kwargs):
        self.callback = callback
        self.entry_row = Adw.EntryRow(title=_("Enter text")) if entry_row is None else entry_row
        self.regex = regex

        group = Adw.PreferencesGroup()
        group.add(self.entry_row)

        super().__init__(*args, **kwargs, child=group)

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
        self._on_response("submit")

    def _on_input_changed(self, *_) -> None:
        if self.input_invalid:
            self.input_invalid = False
            self.entry_row.remove_css_class("error")
            self.popover.popdown()

    @override
    def _on_response(self, response_id: str) -> None:
        text = self.entry_row.get_text()

        if self.regex is not None and not self.regex.match(text):
            self.input_invalid = True
            self.entry_row.add_css_class("error")
            self.popover.popup()
            return

        self.had_response = True

        self.close()
        self.callback(text)


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
    def close(self) -> bool:
        self.force_close()
        return True

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
    options: dict[str, Adw.ActionRow]

    def __init__(self, callback: Callable[[str], Any], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.callback = callback

        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE, css_classes=["boxed-list"])
        self.set_extra_child(self.list_box)

        self.add_response("submit", _("Confirm"))
        self.set_response_appearance("submit", Adw.ResponseAppearance.SUGGESTED)

        self.options = {}

    def add_option(self, key: str, value: str) -> None:
        btn = Gtk.CheckButton(can_focus=False)
        row = Adw.ActionRow(
            name=key,
            title=value,
            activatable_widget=btn
        )
        row.add_prefix(btn)

        if len(self.options) > 0:
            btn.set_group(cast(Gtk.CheckButton, next(iter(self.options.values())).get_activatable_widget()))

        self.list_box.append(row)
        self.options[key] = row

    def remove_option(self, key: str) -> None:
        if key not in self.options:
            msg = f"No such key: {key}"
            raise ValueError(msg)
        self.list_box.remove(self.options.pop(key))

    def select_option(self, key: str) -> None:
        if key not in self.options:
            msg = f"No such key: {key}"
            raise ValueError(msg)
        self.options[key].activate()

    @override
    def _on_response(self, dialog: Adw.AlertDialog, response_id: str) -> None:
        if response_id == "submit":
            for key, row in self.options.items():
                if cast(Gtk.CheckButton, row.get_activatable_widget()).get_active():
                    self.callback(key)


class MultiChooserDialog(ValidationDialog):
    callback: Callable[[list[str]], Any]
    min_choices: int
    max_choices: int
    incompatible_options: list[list[str]] | None
    selected_options: list[str]
    list_box: Gtk.ListBox
    options: dict[str, Adw.ActionRow]

    def __init__(self, callback: Callable[[list[str]], Any], min_choices: int = 0, max_choices: int = -1,
                 incompatible_options: list[list[str]] | None = None, *args, **kwargs):
        self.callback = callback
        self.min_choices = min_choices
        self.max_choices = max_choices
        self.incompatible_options = incompatible_options
        self.selected_options = []

        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE, css_classes=["boxed-list"])

        super().__init__(*args, **kwargs, child=self.list_box)

        self.options = {}

    def add_option(self, key: str, value: str) -> None:
        btn = Gtk.CheckButton(can_focus=False)
        row = Adw.ActionRow(
            name=key,
            title=value,
            activatable_widget=btn
        )
        row.add_prefix(btn)

        btn.connect("toggled", self._on_toggle, row)

        self.list_box.append(row)
        self.options[key] = row

    def remove_option(self, key: str) -> None:
        if key not in self.options:
            msg = f"No such key: {key}"
            raise ValueError(msg)
        self.list_box.remove(self.options.pop(key))

    def select_option(self, key: str) -> None:
        if key not in self.options:
            msg = f"No such key: {key}"
            raise ValueError(msg)
        self.options[key].activate()

    def _on_toggle(self, btn: Gtk.CheckButton, row: Adw.ActionRow) -> None:
        if btn.get_active():
            self.selected_options.append(row.get_name())
        else:
            self.selected_options.remove(row.get_name())

        disabled_options: list[str] = []
        if self.incompatible_options is not None:
            for selected_option in self.selected_options:
                for incompatible_options_sub in self.incompatible_options:
                    if selected_option in incompatible_options_sub:
                        disabled_options.extend(filter(lambda e: e != selected_option, incompatible_options_sub))

        for key, _row in self.options.items():
            disable_max = (self.max_choices != -1 and key not in self.selected_options
                           and len(self.selected_options) == self.max_choices)

            _row.set_sensitive(key not in disabled_options and not disable_max)

            if disable_max:
                _row.set_tooltip_text(_("You can't select more than {0} options.").format(self.max_choices))
            elif key in disabled_options:
                _row.set_tooltip_text(_("You can't select this option, as it is incompatible with the "
                                        "following already selected option(s): {0}.")
                                      .format(", ".join(f"'{self.options[e].get_title()}'"
                                                        for e in self.__calculate_incompatible_causes(key))))
            else:
                _row.set_tooltip_text()

    def __calculate_incompatible_causes(self, option: str) -> list[str]:
        causes: list[str] = []

        if self.incompatible_options is not None:
            for incompatible_options_sub in self.incompatible_options:
                if option in incompatible_options_sub:
                    causes.extend(filter(lambda e: e in self.selected_options, incompatible_options_sub))

        return causes

    @override
    def _on_response(self, response_id: str) -> None:
        if len(self.selected_options) < self.min_choices:
            dialog = TextDialog(
                heading=_("Invalid selection"),
                body=_("You must select at least {0} option(s).").format(self.min_choices)
            )
            dialog.present(self)
            return

        self.had_response = True

        self.callback(self.selected_options)
        self.close()


class ErrorDialog(ValidationDialog):
    callback: Callable[[], Any] | None

    def __init__(self, *args, error: Exception, button_label: str, destructive: bool = False,
                 callback: Callable[[], Any] | None = None, **kwargs):

        buttons = {
            "report": (_("Report bug"), "suggested-action"),
            "close": (button_label, "destructive-action" if destructive else None)
        }

        super().__init__(*args, **kwargs, child=ErrorDetails(error=error), buttons=buttons)

        self.callback = callback

    @override
    def _on_response(self, response_id: str) -> None:
        if response_id == "report":
            Gio.AppInfo.launch_default_for_uri_async(SBCC_ISSUES_PAGE)
            return

        self.had_response = True

        if self.callback is not None:
            self.callback()
        self.close()
