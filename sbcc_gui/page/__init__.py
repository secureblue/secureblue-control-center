# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from gi.repository import Adw
from sbcc_framework.feature import Category
from sbcc_gui.window import Toastable


class PreferencesGroup(Adw.PreferencesGroup):
    priority: int

    def __init__(self, priority: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.priority = priority

    def get_priority(self) -> int:
        return self.priority


class FeaturesPage(Adw.PreferencesPage):
    main_window: Toastable
    categories: dict[str, PreferencesGroup]

    def __init__(self, main_window: Toastable, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.categories = {}

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

                    self.insert(new_group, i)
                    break
                if i == len(self.categories) - 1:
                    self.categories[category.name] = new_group
                    self.add(new_group)
        else:
            self.categories[category.name] = new_group
            self.add(new_group)
