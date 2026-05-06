# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from typing import Final
from gi.repository import Adw, Gtk, GLib
from sbcc_framework.feature import Category
from sbcc_gui.window import Toastable
from sbcc_util import gettext_marker

_: Final = gettext_marker()


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
    priority: int

    def __init__(self, priority: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.priority = priority

    def get_priority(self) -> int:
        return self.priority


class FeaturesPage(Adw.Bin):
    main_window: Toastable
    stack: Adw.ViewStack
    page: Adw.PreferencesPage
    categories: dict[str, PreferencesGroup]
    ready: bool = False
    loading: int = 0

    def __init__(self, title: str, main_window: Toastable, *args, **kwargs) -> None:
        super().__init__()

        self.main_window = main_window
        self.stack = Adw.ViewStack()
        self.page = Adw.PreferencesPage(title=title, *args, **kwargs)
        self.categories = {}

        self.stack.add_named(LoadingPage(label=_("Loading {0}...").format(title)), "loading")
        self.stack.add_named(self.page, "main")

        self.stack.set_visible_child_name("loading")

        self.set_child(self.stack)

    def feature_loading(self) -> None:
        self.loading += 1

    def feature_loaded(self) -> None:
        self.loading -= 1
        self.__check_done_loading()

    def features_ready(self) -> None:
        self.ready = True
        self.__check_done_loading()

    def __check_done_loading(self) -> None:
        if self.ready and self.loading == 0:
            GLib.idle_add(lambda: self.stack.set_visible_child_name("main"))

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
