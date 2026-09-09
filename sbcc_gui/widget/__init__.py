# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

import traceback

from collections.abc import Callable
from typing import Final, override
from gi.repository import Gtk, Adw
from sbcc_util import gettext_marker

_: Final[Callable[[str], str]] = gettext_marker()


class Banner(Adw.Bin):
    child: Adw.Bin
    revealer: Gtk.Revealer
    label: Gtk.Label

    def __init__(self, *args, child: Gtk.Widget | None = None, **kwargs):
        super().__init__(*args, **kwargs, valign=Gtk.Align.START)

        self.child = Adw.Bin()
        self.revealer = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.label = Gtk.Label(css_classes=["heading"])

        outer_box = Gtk.Box(hexpand=True, css_classes=["view"])

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10,
                      margin_top=15, margin_bottom=15, halign=Gtk.Align.CENTER, hexpand=True)
        box.append(self.child)
        box.append(self.label)
        outer_box.append(box)

        self.revealer.set_child(outer_box)

        super().set_child(self.revealer)

        self.child.set_child(child)

    @override
    def set_child(self, child: Gtk.Widget | None = None) -> None:
        self.child.set_child(child)

    def reveal(self, text: str) -> None:
        self.label.set_text(text)
        self.revealer.set_reveal_child(True)

    def collapse(self) -> None:
        self.revealer.set_reveal_child(False)


class ErrorDetails(Adw.Bin):
    def __init__(self, *args, error: Exception, **kwargs):
        super().__init__(*args, **kwargs)

        list_box = Gtk.ListBox()
        list_box.add_css_class("boxed-list")
        list_box.add_css_class("error")

        error_details = Adw.ExpanderRow(title=_("Error details"))
        error_details.add_row(Gtk.ScrolledWindow(
            child=Gtk.TextView(
                editable=False,
                monospace=True,
                wrap_mode=Gtk.WrapMode.NONE,
                vexpand=True,
                hexpand=True,
                buffer=Gtk.TextBuffer(
                    text="".join(traceback.format_exception(type(error), error, error.__traceback__))
                ),
                top_margin=10,
                right_margin=10,
                bottom_margin=10,
                left_margin=10
            ),
            min_content_width=500,
            vscrollbar_policy=Gtk.PolicyType.NEVER
        ))
        list_box.append(error_details)

        self.set_child(list_box)
