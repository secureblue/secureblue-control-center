# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from gi.repository import Adw


class Sidebar(Adw.Bin):
    sidebar: Adw.ViewSwitcherSidebar

    def __init__(self, *args, stack: Adw.ViewStack, **kwargs):
        super().__init__(*args, **kwargs)

        self.sidebar = Adw.ViewSwitcherSidebar()
        self.sidebar.set_stack(stack)

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(Adw.HeaderBar())
        toolbar_view.set_content(self.sidebar)

        self.set_child(toolbar_view)
