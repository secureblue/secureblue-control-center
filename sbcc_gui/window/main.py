# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from threading import Thread
from typing import Final, Any, override
from gi.repository import Adw, GLib, Gio, Gtk
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.preference import Preference, MultiPreference
from sbcc_framework.feature.utility import Utility
from sbcc_framework.presenter import Presenter
from sbcc_gui import UserCancelFeatureException, FeatureException, on_gtk_thread
from sbcc_gui.page.utilities import UtilitiesPage
from sbcc_gui.page.home import HomePage
from sbcc_gui.page.preferences import PreferencesPage
from sbcc_gui.presenter import GUIPresenter
from sbcc_gui.widget import Banner
from sbcc_gui.widget.dialog import ErrorDialog, TextDialog
from sbcc_gui.widget.row import SidebarRow, PreferenceRow, MultiPreferenceRow, FeatureRow, UtilityRow
from sbcc_gui.widget.sidebar import Sidebar
from sbcc_gui.window import Toastable
from sbcc_util import gettext_marker, SBCC_VERSION, SBCC_ISSUES_PAGE, SBCC_WEBSITE, SBCC_APPLICATION_ID, \
    require_not_none

_: Final[Callable[[str], str]] = gettext_marker()


class MainWindow(Adw.ApplicationWindow, Toastable):
    about: Adw.AboutDialog
    toast_overlay: Adw.ToastOverlay
    sidebar: Sidebar
    stack: Adw.ViewStack
    banner: Banner

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
        about_action.connect("activate", lambda *_: self.__show_about())
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

        overlay = Gtk.Overlay()

        self.banner = Banner(child=Adw.Spinner())
        overlay.add_overlay(self.banner)

        overlay.set_child(self.stack)

        self.toast_overlay.set_child(overlay)

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
    @on_gtk_thread()
    def show_toast(self, toast: Adw.Toast) -> None:
        self.toast_overlay.add_toast(toast)

    def add_preference(self, compiled: CompiledFeature[Preference]) -> None:
        def on_toggle(wrapper: PreferenceRow) -> None:
            self.__handle_feature(
                compiled,
                wrapper,
                wrapper.get_row().get_active,
                compiled.feature.get_state,
                compiled.feature.set_state,
                wrapper.get_row().set_active
            )

        self.preferences_page.add_preference(compiled, on_toggle)

    def add_multi_preference(self, compiled: CompiledFeature[MultiPreference]) -> None:
        def on_change(wrapper: MultiPreferenceRow) -> None:
            self.__handle_feature(
                compiled,
                wrapper,
                wrapper.get_selected_option,
                compiled.feature.get_state,
                compiled.feature.set_state,
                wrapper.set_selected_option
            )

        self.preferences_page.add_multi_preference(compiled, on_change)

    def add_utility(self, compiled: CompiledFeature[Utility]) -> None:
        def on_run(wrapper: UtilityRow) -> None:
            self.__handle_feature(
                compiled,
                wrapper,
                lambda: None,
                lambda: None,
                lambda presenter, _: compiled.feature.run(presenter),
                lambda _: None
            )

        self.utilities_page.add_utility(compiled, on_run)

    # ruff: ignore[PLR0913, PLR0917]
    def __handle_feature[T](self,
                            compiled: CompiledFeature,
                            row: FeatureRow,
                            gui_getter: Callable[[], T],
                            feature_getter: Callable[[], T],
                            feature_setter: Callable[[Presenter, T], T],
                            gui_setter: Callable[[T], Any]) -> None:
        self.__feature_start(compiled)

        def run(_state: T) -> None:
            @on_gtk_thread()
            def apply_state(state: T) -> None:
                if gui_getter() != state:
                    row.block_handler()
                    gui_setter(state)
                    row.unblock_handler()

            def cancel_func() -> None:
                try:
                    _current_state = feature_getter()
                except Exception as __e:
                    _ex = FeatureException(f"Failed to get state of feature {compiled} while running cancel func")
                    row.disable_with_error(_ex, True)
                    self.__feature_finished()
                    raise _ex from __e

                apply_state(_current_state)
                self.__feature_finished()

                _msg = (f"User cancelled feature {compiled}"
                        f"{f", reset to {_current_state}" if _current_state is not None else ""}")
                raise UserCancelFeatureException(_msg)

            try:
                current_state = feature_getter()
            except Exception as e:
                ex = FeatureException(f"Failed to get state of feature {compiled}")
                row.disable_with_error(ex, True)
                self.__feature_finished()
                raise ex from e

            if current_state is not None and current_state == _state:
                self.__preference_changed_toast()
                return

            try:
                resulting_state = feature_setter(GUIPresenter(self, compiled, cancel_func), _state)
            except UserCancelFeatureException:
                return
            except FeatureException:
                raise
            except Exception as e:
                try:
                    current_state = feature_getter()
                except Exception as _e:
                    ex = FeatureException(f"Failed to get state of feature {compiled} while handling setter error")
                    row.disable_with_error(ex, True)
                    self.__feature_finished()
                    raise ex from _e

                apply_state(current_state)

                ex = FeatureException(f"Uncaught exception in feature {compiled}"
                                      f"{f", reset to {current_state}" if current_state is not None else ""}")
                self.__show_feature_error_graceful(compiled, ex)
                self.__feature_finished()
                raise ex from e

            apply_state(resulting_state)
            self.__feature_finished()

        Thread(name=f"sbcc_gui:{compiled.name}:run", target=run, args=(gui_getter(),)).start()

    def __feature_start(self, compiled: CompiledFeature) -> None:
        self.__block_ui()
        self.banner.reveal(_('"{0}" is running...').format(compiled.display_name))

    @on_gtk_thread()
    def __feature_finished(self) -> None:
        self.banner.collapse()
        self.__unblock_ui()

    def __block_ui(self) -> None:
        self.sidebar.set_sensitive(False)
        self.stack.set_sensitive(False)

    def __unblock_ui(self) -> None:
        self.sidebar.set_sensitive(True)
        self.stack.set_sensitive(True)

    def __show_about(self) -> None:
        self.about.present(self)

    @on_gtk_thread()
    def __preference_changed_toast(self) -> None:
        self.show_toast(Adw.Toast(
            title=_("Preference was changed externally"),
            timeout=5,
            button_label=_("More information"),
            action_name="win.pref_changed_dialog"
        ))
        self.__feature_finished()

    def __preference_changed_dialog(self) -> None:
        dialog = TextDialog(
            heading=_("Information"),
            body=_("This preference was changed by an external process while the application was open. "
                   "Your selected state is already applied, so no further action is needed.")
        )
        dialog.choose(self)

    @on_gtk_thread()
    def __show_feature_error_graceful(self, compiled: CompiledFeature, error: Exception) -> None:
        dialog = ErrorDialog(
            heading=_("Error"),
            body=(_('The feature "{0}" was aborted due to an unexpected error.\n\n')
                  + _("If the issue persists, please file a bug report with error details attached "
                      "via the button below."))
            .format(compiled.display_name),
            error=error,
            button_label=_("Acknowledge")
        )
        dialog.present(self)
