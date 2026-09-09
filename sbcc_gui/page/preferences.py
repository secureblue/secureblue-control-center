# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from threading import Thread
from typing import Any, Final
from sbcc_framework.feature import CompiledFeature
from sbcc_framework.feature.preference import Preference, MultiPreference
from sbcc_gui import FeatureException, on_gtk_thread
from sbcc_gui.page import FeaturesPage
from sbcc_gui.widget.row import PreferenceRow, MultiPreferenceRow, FeatureRow
from sbcc_util import gettext_marker

_: Final[Callable[[str], str]] = gettext_marker()


class PreferencesPage(FeaturesPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, title=_("Preferences"))

    def add_preference(self, compiled: CompiledFeature[Preference], callback: Callable[[PreferenceRow], Any]) -> None:
        wrapper = self.initialize_preference(
            compiled,
            callback,
            PreferenceRow,
            compiled.feature.get_state,
            lambda _wrapper, state: _wrapper.get_row().set_active(state)
        )

        self.categories[compiled.category.name].add(wrapper.get_row())

    def add_multi_preference(self, compiled: CompiledFeature[MultiPreference],
                             callback: Callable[[MultiPreferenceRow], Any]) -> None:
        def initialize(_wrapper: MultiPreferenceRow, state: tuple[dict[str, str], str]) -> None:
            for key, value in state[0].items():
                _wrapper.add_option(key, value)
            _wrapper.set_selected_option(state[1])

        wrapper = self.initialize_preference(
            compiled,
            callback,
            MultiPreferenceRow,
            lambda: (compiled.feature.get_options(), compiled.feature.get_state()),
            initialize
        )

        self.categories[compiled.category.name].add(wrapper.get_row())

    def initialize_preference[R: FeatureRow, T](self,
                                                compiled: CompiledFeature,
                                                callback: Callable[[R], Any],
                                                wrapper_constructor: Callable[[CompiledFeature, FeaturesPage,
                                                                               Callable[[R], Any]], R],
                                                feature_getter: Callable[[], T],
                                                feature_initializer: Callable[[R, T], Any]) -> R:
        self.feature_loading()

        category_name = compiled.category.name
        if category_name not in self.categories:
            self.insert_category(compiled.category)

        wrapper = wrapper_constructor(compiled, self, callback)

        def initialize(_compiled: CompiledFeature, _wrapper: R) -> None:
            @on_gtk_thread()
            def apply_initial_state(_wrapper: R, _state: T) -> None:
                _wrapper.block_handler()
                feature_initializer(_wrapper, _state)
                _wrapper.unblock_handler()

                self.feature_loaded()

            @on_gtk_thread()
            def disable_preference(_wrapper: R, reason: str) -> None:
                row = _wrapper.get_row()
                row.set_tooltip_text(_("This preference is not available: {0}").format(reason))
                row.set_sensitive(False)

                self.feature_loaded()

            try:
                unavailable_context = _compiled.feature.is_available()
                if unavailable_context is not None:
                    disable_preference(wrapper, unavailable_context)
                    return

                state = feature_getter()
                apply_initial_state(wrapper, state)
            except Exception as e:
                _wrapper.disable_with_error(e, False)
                self.feature_load_error(compiled, e)
                msg = f"Failed to initialize feature {compiled}"
                raise FeatureException(msg) from e

        Thread(name=f"sbcc_gui:{compiled.name}:initialize", target=initialize,
               args=(compiled, wrapper)).start()

        return wrapper
