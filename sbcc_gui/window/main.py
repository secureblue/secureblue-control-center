# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from threading import Event, Thread
from typing import Final, Any, override
from gi.repository import Adw, GLib, Gio, Gtk
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.preference import Preference, MultiPreference
from sbcc_framework.feature.utility import Utility
from sbcc_gui.page.utilities import UtilitiesPage
from sbcc_gui.widget.dialog import FatalErrorDialog, TextDialog
from sbcc_gui.widget.row import SidebarRow, PreferenceRow, MultiPreferenceRow
from sbcc_gui.page.home import HomePage
from sbcc_gui.page.preferences import PreferencesPage
from sbcc_gui.presenter import GUIPresenter
from sbcc_gui.widget.sidebar import Sidebar
from sbcc_gui.window import Toastable
from sbcc_util import UserCancelFeatureException, gettext_marker, SBCC_VERSION, SBCC_ISSUES_PAGE, SBCC_WEBSITE, \
    SBCC_APPLICATION_ID, require_not_none

_: Final[Callable[[str], str]] = gettext_marker()


class MainWindow(Adw.ApplicationWindow, Toastable):
    about: Adw.AboutDialog
    toast_overlay: Adw.ToastOverlay
    sidebar: Sidebar
    stack: Adw.ViewStack

    preferences_page: PreferencesPage
    utilities_page: UtilitiesPage

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(800, 700)

        application_name = require_not_none(GLib.get_application_name())

        self.about = Adw.AboutDialog(
            application_name=application_name,
            application_icon=SBCC_APPLICATION_ID,
            developer_name="The secureblue authors",
            developers=["pxlkng"],
            version=SBCC_VERSION,
            website=SBCC_WEBSITE,
            issue_url=SBCC_ISSUES_PAGE
        )

        menu = Gio.Menu().new()
        about_action = Gio.SimpleAction.new("about")
        about_action.connect("activate", lambda *_: self.show_about())
        self.add_action(about_action)
        menu.append(_("About"), "win.about")

        pref_changed_action = Gio.SimpleAction.new("pref_changed_dialog")
        pref_changed_action.connect("activate", lambda *_: self.__preference_changed_dialog())
        self.add_action(pref_changed_action)

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
        splitview.set_content(Adw.NavigationPage(title=application_name, child=toolbar_view))
        self.sidebar = Sidebar()
        splitview.set_sidebar(Adw.NavigationPage(title=_("Menu"), child=self.sidebar))
        self.set_content(splitview)

        self.stack = Adw.ViewStack()
        self.stack.set_enable_transitions(True)
        self.stack.set_transition_duration(150)

        self.toast_overlay.set_child(self.stack)

        # Home Page
        self.stack.add_named(HomePage(), "home")
        self.sidebar.add_entry(
            SidebarRow(name="home", label=_("Home"), icon_name="go-home-symbolic"),
            lambda: self.stack.set_visible_child_name("home")
        )

        # Preferences Page
        self.preferences_page = PreferencesPage(main_window=self)
        self.stack.add_named(self.preferences_page, "preferences")
        self.sidebar.add_entry(
            SidebarRow(name="preferences", label=_("Preferences"), icon_name="preferences-system-symbolic"),
            lambda: self.stack.set_visible_child_name("preferences")
        )

        # Utilities Page
        self.utilities_page = UtilitiesPage(main_window=self)
        self.stack.add_named(self.utilities_page, "utilities")
        self.sidebar.add_entry(
            SidebarRow(name="utilities", label=_("Utilities"), icon_name="utilities-terminal-symbolic"),
            lambda: self.stack.set_visible_child_name("utilities")
        )

    @override
    def show_toast(self, toast: Adw.Toast) -> None:
        self.toast_overlay.add_toast(toast)

    def add_preference(self, compiled: CompiledFeature[Preference]) -> None:
        def on_toggle(wrapper: PreferenceRow) -> None:
            self.sidebar.set_sensitive(False)
            self.stack.set_sensitive(False)

            def do_toggle(_state: bool) -> None:
                def apply_result(_result: bool) -> None:
                    if wrapper.get_row().get_active() != _result:
                        wrapper.block_handler()
                        wrapper.get_row().set_active(_result)
                        wrapper.unblock_handler()
                    self.sidebar.set_sensitive(True)
                    self.stack.set_sensitive(True)

                def cancel_func() -> None:
                    def get_state(_event: Event, _result: list[bool]) -> None:
                        try:
                            _result[0] = compiled.feature.get_state()
                        except Exception as _e:
                            self.show_error_and_exit(compiled, _e)
                            return

                        _event.set()

                    _result: list[bool] = [False]
                    event = Event()
                    Thread(name=f"sbcc_gui:{compiled.name}:get-state", target=get_state, args=(event, _result)).start()
                    event.wait()
                    GLib.idle_add(apply_result, _result[0])

                    msg = f"User cancelled preference {compiled}, reset to {_result[0]}"
                    raise UserCancelFeatureException(msg)

                try:
                    current_state = compiled.feature.get_state()

                    if current_state == _state:
                        GLib.idle_add(self.__preference_changed_toast)
                        return

                    result = compiled.feature.set_state(GUIPresenter(self, compiled, cancel_func), _state)
                except UserCancelFeatureException:
                    raise
                except Exception as e:
                    self.show_error_and_exit(compiled, e)
                    return

                GLib.idle_add(apply_result, result)

            Thread(name=f"sbcc_gui:{compiled.name}:do-toggle", target=do_toggle,
                   args=(wrapper.get_row().get_active(),)).start()

        self.preferences_page.add_preference(compiled, on_toggle)

    def add_multi_preference(self, compiled: CompiledFeature[MultiPreference]) -> None:
        def on_change(wrapper: MultiPreferenceRow) -> None:
            self.sidebar.set_sensitive(False)
            self.stack.set_sensitive(False)

            def do_change(_state: str) -> None:
                def apply_result(_result: str) -> None:
                    if wrapper.get_selected_option() != _result:
                        wrapper.block_handler()
                        wrapper.set_selected_option(_result)
                        wrapper.unblock_handler()
                    self.sidebar.set_sensitive(True)
                    self.stack.set_sensitive(True)

                def cancel_func() -> None:
                    def get_state(_event: Event, _result: list[str]) -> None:
                        try:
                            _result[0] = compiled.feature.get_state()
                        except Exception as _e:
                            self.show_error_and_exit(compiled, _e)
                            return

                        _event.set()

                    _result: list[str] = [""]
                    event = Event()
                    Thread(name=f"sbcc_gui:{compiled.name}:get-state", target=get_state, args=(event, _result)).start()
                    event.wait()
                    GLib.idle_add(apply_result, _result[0])

                    msg = f"User cancelled preference {compiled}, reset to {_result[0]}"
                    raise UserCancelFeatureException(msg)

                try:
                    current_state = compiled.feature.get_state()

                    if current_state == _state:
                        GLib.idle_add(self.__preference_changed_toast)
                        return

                    result = compiled.feature.set_state(GUIPresenter(self, compiled, cancel_func), _state)
                except UserCancelFeatureException:
                    raise
                except Exception as e:
                    self.show_error_and_exit(compiled, e)
                    return

                GLib.idle_add(apply_result, result)

            Thread(name=f"sbcc_gui:{compiled.name}:do-change", target=do_change,
                   args=(wrapper.get_selected_option(),)).start()

        self.preferences_page.add_multi_preference(compiled, on_change)

    def __preference_changed_toast(self) -> None:
        self.show_toast(Adw.Toast(
            title=_("Preference was changed externally"),
            timeout=5,
            button_label=_("More information"),
            action_name="win.pref_changed_dialog"
        ))
        self.sidebar.set_sensitive(True)
        self.stack.set_sensitive(True)

    def __preference_changed_dialog(self) -> None:
        dialog = TextDialog(
            heading=_("Information"),
            body=_("This preference was changed by an external process while the application was open. "
                   "Your selected state is already applied, so no further action is needed.")
        )
        dialog.choose(self)

    def add_utility(self, compiled: CompiledFeature[Utility]) -> None:
        def on_run(_: Any) -> None:
            self.sidebar.set_sensitive(False)
            self.stack.set_sensitive(False)

            def do_run() -> None:
                def unblock_ui() -> None:
                    self.sidebar.set_sensitive(True)
                    self.stack.set_sensitive(True)

                def cancel_func() -> None:
                    unblock_ui()

                    msg = f"User cancelled utility {compiled}"
                    raise UserCancelFeatureException(msg)

                try:
                    compiled.feature.run(GUIPresenter(self, compiled, cancel_func))
                except UserCancelFeatureException:
                    raise
                except Exception as e:
                    self.show_error_and_exit(compiled, e)
                    return

                GLib.idle_add(unblock_ui)

            Thread(name=f"sbcc_gui:{compiled.name}:do-run", target=do_run).start()

        self.utilities_page.add_utility(compiled, on_run)

    def show_about(self) -> None:
        self.about.present(self)

    @override
    def show_error_and_exit(self, feature: CompiledFeature, e: Exception) -> None:
        def show_error() -> None:
            dialog = FatalErrorDialog(callback=lambda: require_not_none(self.get_application()).quit())
            dialog.present(self)

        GLib.idle_add(show_error)

        msg = f"Uncaught exception in feature {feature}"
        raise RuntimeError(msg, e)
