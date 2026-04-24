# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from threading import Event, Thread
from typing import Final
from gi.repository import Adw, GLib, Gio, Gtk
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.toggle import Toggle
from sbcc_framework.feature.utility import Utility
from sbcc_gui.page.utilities import UtilitiesPage
from sbcc_gui.widget.dialog import FatalErrorDialog
from sbcc_gui.widget.row import SidebarRow, ToggleRow
from sbcc_gui.page.home import HomePage
from sbcc_gui.page.toggles import TogglesPage
from sbcc_gui.presenter import GUIPresenter
from sbcc_gui.widget.sidebar import Sidebar
from sbcc_gui.window import Toastable
from util import UserCancelFeatureException, gettext_marker, SBCC_VERSION

_: Final = gettext_marker()


class MainWindow(Adw.ApplicationWindow, Toastable):
    about: Adw.AboutDialog
    toast_overlay: Adw.ToastOverlay
    sidebar: Sidebar
    stack: Adw.ViewStack

    toggles_page: TogglesPage
    utilities_page: UtilitiesPage

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(800, 700)

        self.about = Adw.AboutDialog(
            application_name=GLib.get_application_name(),
            application_icon=self.get_application().get_application_id(),
            developer_name="The secureblue authors",
            developers=["PXLKNG"],
            version=SBCC_VERSION
        )

        menu = Gio.Menu().new()
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.show_about)
        self.add_action(about_action)
        menu.append(_("About"), "win.about")

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.pack_end(Gtk.MenuButton(
            icon_name="open-menu-symbolic",
            popover=Gtk.PopoverMenu(menu_model=menu)
        ))
        toolbar_view.add_top_bar(header)

        self.toast_overlay = Adw.ToastOverlay()
        toolbar_view.set_content(self.toast_overlay)

        splitview = Adw.NavigationSplitView()
        splitview.set_content(Adw.NavigationPage(title=GLib.get_application_name(), child=toolbar_view))
        self.sidebar = Sidebar()
        splitview.set_sidebar(Adw.NavigationPage(title=_("Menu"), child=self.sidebar))
        self.set_content(splitview)

        self.stack = Adw.ViewStack()
        self.toast_overlay.set_child(self.stack)

        # Home Page
        self.stack.add_named(HomePage(), "home")
        self.sidebar.add_entry(
            SidebarRow(name="home", label=_("Home"), icon_name="go-home-symbolic"),
            lambda: self.stack.set_visible_child_name("home")
        )

        # Toggles Page
        self.toggles_page = TogglesPage(main_window=self)
        self.stack.add_named(self.toggles_page, "toggles")
        self.sidebar.add_entry(
            SidebarRow(name="toggles", label=_("Toggles"), icon_name="preferences-system-symbolic"),
            lambda: self.stack.set_visible_child_name("toggles")
        )

        # Utilities Page
        self.utilities_page = UtilitiesPage(main_window=self)
        self.stack.add_named(self.utilities_page, "utilities")
        self.sidebar.add_entry(
            SidebarRow(name="utilities", label=_("Utilities"), icon_name="utilities-terminal-symbolic"),
            lambda: self.stack.set_visible_child_name("utilities")
        )

    def show_toast(self, toast: Adw.Toast) -> None:
        self.toast_overlay.add_toast(toast)

    def add_toggle(self, compiled: CompiledFeature[Toggle]) -> None:
        # noinspection PyUnusedLocal
        def on_toggle(wrapper: ToggleRow, *args, __capture: CompiledFeature[Toggle] = compiled) -> None:
            self.sidebar.set_sensitive(False)
            self.stack.set_sensitive(False)

            def do_toggle(_state: bool) -> None:
                def apply_result(_result: bool) -> None:
                    self.sidebar.set_sensitive(True)
                    self.stack.set_sensitive(True)
                    wrapper.block_handler()
                    wrapper.get_row().set_active(_result)
                    wrapper.unblock_handler()

                def cancel_func() -> None:
                    def get_state(_event: Event, _result: list[bool]) -> None:
                        try:
                            _result[0] = __capture.feature.get_state()
                        except UserCancelFeatureException:
                            raise
                        except Exception as _e:
                            self.show_error_and_exit(__capture, _e)
                            return

                        _event.set()

                    _result: list[bool] = [False]
                    event = Event()
                    Thread(name=f"sbcc_gui:{__capture.name}:get-state", target=get_state, args=(event, _result)).start()
                    event.wait()
                    GLib.idle_add(apply_result, _result[0])

                    raise UserCancelFeatureException(f"User cancelled toggle {compiled.name}, reset to {_result[0]}")

                try:
                    result = __capture.feature.set_state(GUIPresenter(self, __capture, cancel_func), _state)
                except UserCancelFeatureException:
                    raise
                except Exception as e:
                    self.show_error_and_exit(__capture, e)
                    return

                GLib.idle_add(apply_result, result)

            Thread(name=f"sbcc_gui:{__capture.name}:do-toggle", target=do_toggle,
                   args=(wrapper.get_row().get_active(),)).start()

        self.toggles_page.add_toggle(compiled, on_toggle)

    def add_utility(self, compiled: CompiledFeature[Utility]) -> None:
        # noinspection PyUnusedLocal
        def on_run(*args, __capture: CompiledFeature[Utility] = compiled) -> None:
            self.sidebar.set_sensitive(False)
            self.stack.set_sensitive(False)

            def do_run() -> None:
                def unblock_ui() -> None:
                    self.sidebar.set_sensitive(True)
                    self.stack.set_sensitive(True)

                def cancel_func() -> None:
                    unblock_ui()
                    raise UserCancelFeatureException(f"User cancelled utility {compiled.name}")

                try:
                    __capture.feature.run(GUIPresenter(self, __capture, cancel_func))
                except UserCancelFeatureException:
                    raise
                except Exception as e:
                    self.show_error_and_exit(__capture, e)
                    return

                GLib.idle_add(unblock_ui)

            Thread(name=f"sbcc_gui:{__capture.name}:do-run", target=do_run).start()

        self.utilities_page.add_utility(compiled, on_run)

    # noinspection PyUnusedLocal
    def show_about(self, *args) -> None:
        self.about.present(self)

    def show_error_and_exit(self, feature: CompiledFeature, e: Exception) -> None:
        def show_error() -> None:
            dialog = FatalErrorDialog(callback=lambda: self.get_application().quit())
            dialog.present(self)

        GLib.idle_add(show_error)

        raise RuntimeError(f"Uncaught exception in feature {feature}", e)
