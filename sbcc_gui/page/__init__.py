# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Final, override
from gi.repository import Adw, Gtk, GLib, Gio
from sbcc_framework.feature import Category, CompiledFeature
from sbcc_gui import on_gtk_thread
from sbcc_gui.widget import ErrorDetails
from sbcc_gui.window import Toastable
from sbcc_util import gettext_marker, require_not_none, SBCC_ISSUES_PAGE

_: Final[Callable[[str], str]] = gettext_marker()


class LoadingPage(Adw.Bin):
    label: Gtk.Label

    def __init__(self, label: str):
        super().__init__()

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.CENTER
        )
        box.append(Adw.Spinner())
        self.label = Gtk.Label(margin_top=10)
        self.set_label(label)
        box.append(self.label)

        self.set_child(box)

    def set_label(self, label: str) -> None:
        self.label.set_markup(f"<b>{label}</b>")


class PreferencesGroup(Adw.PreferencesGroup):
    store: Gio.ListStore[Adw.PreferencesRow]
    priority: int

    def __init__(self, priority: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.store = Gio.ListStore.new(Adw.PreferencesRow)
        self.priority = priority

        self.bind_model(self.store, lambda row: row)

    @override
    def add(self, child: Gtk.Widget) -> None:
        if not isinstance(child, Adw.PreferencesRow):
            msg = "Child must be Adw.PreferencesRow"
            raise ValueError(msg)
        self.store.append(child)

    def insert(self, index: int, child: Adw.PreferencesRow) -> None:
        self.store.insert(index, child)

    def replace(self, old_child: Adw.PreferencesRow, new_child: Adw.PreferencesRow) -> None:
        index = require_not_none(self.get_index(old_child))
        self.remove_at_index(index)
        self.insert(index, new_child)

    def remove_at_index(self, index: int) -> None:
        self.store.remove(index)

    @override
    def remove(self, child: Gtk.Widget) -> None:
        if not isinstance(child, Adw.PreferencesRow):
            msg = "Child must be Adw.PreferencesRow"
            raise ValueError(msg)
        self.store.remove(require_not_none(self.get_index(child)))

    def get_index(self, child: Adw.PreferencesRow) -> int | None:
        for i in range(self.store.get_n_items()):
            if self.get_row(i) == child:
                return i
        return None

    def get_priority(self) -> int:
        return self.priority


class ErrorPage(Adw.Bin):
    scroll: Gtk.ScrolledWindow
    queue: list[Gtk.Box]
    callback: Callable[[], None]

    def __init__(self, *args, callback: Callable[[], None], **kwargs):
        super().__init__(*args, **kwargs)

        self.scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.queue = []
        self.callback = callback

        self.set_child(self.scroll)

    @on_gtk_thread()
    def add_error(self, title: str, message: str, error: Exception) -> None:
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.CENTER,
            margin_start=25,
            margin_end=25,
            margin_top=25,
            margin_bottom=25,
            spacing=20,
            vexpand=True
        )

        box.append(
            Gtk.Label(
                label=title,
                css_classes=["heading", "title-3"],
                justify=Gtk.Justification.CENTER
            )
        )
        box.append(
            Gtk.Label(
                label=message,
                wrap=True,
                justify=Gtk.Justification.CENTER
            )
        )
        box.append(
            ErrorDetails(error=error)
        )

        error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True,
                            halign=Gtk.Align.CENTER, margin_bottom=10, spacing=10)

        report_btn = Gtk.Button(label=_("Report bug"))
        report_btn.add_css_class("suggested-action")
        report_btn.connect("clicked", lambda *_: Gio.AppInfo.launch_default_for_uri_async(SBCC_ISSUES_PAGE))
        error_box.append(report_btn)

        next_btn = Gtk.Button(label=_("Acknowledge"))
        next_btn.add_css_class("destructive-action")
        next_btn.connect("clicked", lambda *_: self.__next())
        error_box.append(next_btn)

        box.append(error_box)

        if self.scroll.get_child() is None:
            self.scroll.set_child(box)
        else:
            self.queue.append(box)

    def __next(self) -> None:
        if len(self.queue) > 0:
            self.scroll.set_child(self.queue.pop(0))
        else:
            self.callback()


class FeaturesPage(Adw.Bin):
    main_window: Toastable
    stack: Adw.ViewStack
    page: Adw.PreferencesPage
    error_page: ErrorPage
    categories: dict[str, PreferencesGroup]
    ready: bool = False
    loading: int = 0
    has_error: bool = False

    def __init__(self, title: str, main_window: Toastable, *args, **kwargs) -> None:
        super().__init__()

        self.main_window = main_window
        self.stack = Adw.ViewStack()
        self.page = Adw.PreferencesPage(*args, **kwargs, title=title)
        self.error_page = ErrorPage(callback=lambda: self.stack.set_visible_child_name("main"))
        self.categories = {}

        self.stack.add_named(LoadingPage(label=_("Loading {0}...").format(title)), "loading")
        self.stack.add_named(self.error_page, "error")
        self.stack.add_named(self.page, "main")

        self.stack.set_visible_child_name("loading")

        self.set_child(self.stack)

    def feature_loading(self) -> None:
        self.loading += 1

    def feature_load_error(self, compiled: CompiledFeature, error: Exception) -> None:
        message: str = (_('The feature "{0}" has been disabled due to an unexpected fatal error while initializing.')
                        + " "
                        + _("An application restart is necessary to attempt to restore functionality of the feature.")
                        + "\n\n"
                        + _("If the issue persists, please file a bug report with error details attached "
                            "via the button below.")).format(compiled.display_name)

        self.error_page.add_error(_('Fatal error in "{0}"').format(compiled.display_name), message, error)

        if not self.has_error:
            self.has_error = True
        self.loading -= 1
        self.__check_done_loading()

    def feature_loaded(self) -> None:
        self.loading -= 1
        self.__check_done_loading()

    def features_ready(self) -> None:
        self.ready = True
        self.__check_done_loading()

    def __check_done_loading(self) -> None:
        if self.ready and self.loading == 0:
            GLib.idle_add(lambda: self.stack.set_visible_child_name("main" if not self.has_error else "error"))

    def insert_category(self, category: Category) -> None:
        new_group = PreferencesGroup(
            name=category.name,
            title=category.display_name,
            description=category.description,
            priority=category.priority
        )
        if len(self.categories) > 0:
            for i, group in enumerate(self.categories.copy().values()):
                if new_group.get_priority() > group.get_priority():
                    intermediate = list(self.categories.items())
                    intermediate.insert(i, (category.name, new_group))
                    self.categories = dict(intermediate)

                    self.page.insert(new_group, i)
                    break
                if i == len(self.categories) - 1:
                    self.categories[category.name] = new_group
                    self.page.add(new_group)
        else:
            self.categories[category.name] = new_group
            self.page.add(new_group)
