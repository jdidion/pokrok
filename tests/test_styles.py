"""Tests for pokrok.styles: Widget enum, Style, StyleManager, _resolve_widgets."""

import pytest

from pokrok.styles import Style, StyleManager, Widget, _resolve_widgets


class TestResolveWidgets:
    def test_none_returns_none(self):
        assert _resolve_widgets(None) is None

    def test_empty_list_returns_empty_list(self):
        assert _resolve_widgets([]) == []

    def test_string_names_resolve_to_enum(self):
        assert _resolve_widgets(["BAR", "ETA"]) == [Widget.BAR, Widget.ETA]

    def test_enum_values_passed_through(self):
        assert _resolve_widgets([Widget.SPINNER]) == [Widget.SPINNER]

    def test_mixed_string_and_enum(self):
        assert _resolve_widgets(["BAR", Widget.SPINNER]) == [
            Widget.BAR,
            Widget.SPINNER,
        ]

    def test_unknown_string_raises_keyerror(self):
        with pytest.raises(KeyError):
            _resolve_widgets(["NOT_A_WIDGET"])


class TestStyle:
    def test_default_style_has_no_widgets(self):
        style = Style()
        assert style.sized is None
        assert style.unsized is None

    def test_widgets_apply_to_both_sized_and_unsized(self):
        style = Style(widgets=["BAR", "ETA"])
        assert style.sized == [Widget.BAR, Widget.ETA]
        assert style.unsized == [Widget.BAR, Widget.ETA]

    def test_sized_overrides_widgets_for_sized(self):
        style = Style(widgets=["BAR"], sized=["COUNTER"])
        assert style.sized == [Widget.COUNTER]
        # unsized falls back to widgets since unsized not provided
        assert style.unsized == [Widget.BAR]

    def test_unsized_overrides_widgets_for_unsized(self):
        style = Style(widgets=["BAR"], unsized=["SPINNER"])
        assert style.sized == [Widget.BAR]
        assert style.unsized == [Widget.SPINNER]

    def test_no_widgets_uses_sized_and_unsized_directly(self):
        style = Style(sized=["BAR"], unsized=["SPINNER"])
        assert style.sized == [Widget.BAR]
        assert style.unsized == [Widget.SPINNER]

    def test_get_widgets_selects_by_sized_flag(self):
        style = Style(sized=["BAR"], unsized=["SPINNER"])
        assert style.get_widgets(True) == [Widget.BAR]
        assert style.get_widgets(False) == [Widget.SPINNER]


class TestStyleManager:
    def test_default_style_present(self):
        sm = StyleManager()
        assert "default" in sm
        assert isinstance(sm["default"], Style)

    def test_custom_default_style(self):
        custom = Style(widgets=["BAR"])
        sm = StyleManager(default_style=custom)
        assert sm["default"] is custom

    def test_set_style_options_adds_named_styles(self):
        sm = StyleManager()
        sm.set_style_options({"styles": {"fancy": {"widgets": ["BAR", "ETA"]}}})
        assert "fancy" in sm
        assert sm["fancy"].sized == [Widget.BAR, Widget.ETA]

    def test_set_style_options_default_as_string_reference(self):
        sm = StyleManager()
        sm.set_style_options(
            {
                "styles": {"fancy": {"widgets": ["SPINNER"]}},
                "default_style": "fancy",
            }
        )
        # the default now points at the previously-defined fancy style
        assert sm["default"] is sm["fancy"]

    def test_set_style_options_default_as_inline_config(self):
        sm = StyleManager()
        sm.set_style_options({"default_style": {"widgets": ["COUNTER"]}})
        assert sm["default"].sized == [Widget.COUNTER]

    def test_set_style_options_no_keys_is_noop(self):
        sm = StyleManager()
        before = sm["default"]
        sm.set_style_options({})
        assert sm["default"] is before
