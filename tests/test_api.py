"""Tests for the top-level pokrok API in pokrok/__init__.py.

These exercise ProgressFactory configuration and creation logic plus the
public convenience functions, using the real installed backends.
"""

import json

import pytest

import pokrok
from pokrok.styles import Style, Widget


class TestVersion:
    def test_version_is_a_string(self):
        assert isinstance(pokrok.__version__, str)
        assert pokrok.__version__


class TestDefaultPaths:
    def test_default_paths_includes_cwd_and_home(self, fresh_factory, monkeypatch):
        monkeypatch.chdir("/tmp")
        paths = fresh_factory.default_paths
        assert len(paths) == 2
        assert all(p.endswith("pokrok.json") for p in paths)


class TestConfigureFromFile:
    def test_configure_reads_json_file(self, fresh_factory, tmp_path):
        cfg = tmp_path / "pokrok.json"
        cfg.write_text(json.dumps({"styles": {"x": {"widgets": ["BAR"]}}}))
        fresh_factory.configure(filename=str(cfg))
        assert fresh_factory.configured is True
        assert "x" in fresh_factory.styles

    def test_configure_missing_file_raises(self, fresh_factory, tmp_path):
        missing = tmp_path / "nope.json"
        with pytest.raises(ValueError, match="File not found"):
            fresh_factory.configure(filename=str(missing))

    def test_configure_autodiscovers_default_path(
        self, fresh_factory, monkeypatch, tmp_path
    ):
        monkeypatch.chdir(tmp_path)
        # write a pokrok.json in cwd so default_paths discovers it
        (tmp_path / "pokrok.json").write_text(
            json.dumps({"styles": {"disco": {"widgets": ["SPINNER"]}}})
        )
        # patch home so the second default path does not interfere
        monkeypatch.setenv("HOME", str(tmp_path))
        fresh_factory.configure()
        assert fresh_factory.configured is True
        assert "disco" in fresh_factory.styles

    def test_configure_no_file_found_stays_unconfigured_styles(
        self, fresh_factory, monkeypatch, tmp_path
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        # no pokrok.json anywhere -> configure() runs but finds no file
        fresh_factory.configure()
        # default style still present
        assert "default" in fresh_factory.styles

    def test_configure_with_plugin_names(self, fresh_factory):
        fresh_factory.configure(plugin_names=["tqdm"], exclusive=True)
        assert list(fresh_factory.plugins.plugins) == ["tqdm"]

    def test_configure_with_styles_kwarg(self, fresh_factory):
        fresh_factory.configure(styles={"mine": Style(widgets=["BAR"])})
        assert "mine" in fresh_factory.styles

    def test_configure_from_package_resource(self, fresh_factory):
        # filename of the form "package:resource" loads config via
        # importlib.resources rather than the filesystem.
        fresh_factory.configure(filename="tests:resource_config.json")
        assert fresh_factory.configured is True
        assert "from_resource" in fresh_factory.styles

    def test_configure_bad_resource_spec_raises(self, fresh_factory):
        # a non-existent path with no ':' fails the split, the bare-except
        # swallows it, config stays None, and a ValueError is raised.
        with pytest.raises(ValueError, match="File not found"):
            fresh_factory.configure(filename="this-path-does-not-exist")


class TestCreate:
    def test_create_unsized_returns_meter(self, fresh_factory):
        meter = fresh_factory.create()
        assert meter is not None
        assert meter.is_sized is False

    def test_create_sized_returns_meter(self, fresh_factory):
        meter = fresh_factory.create(size=100)
        assert meter is not None
        assert meter.is_sized is True

    def test_create_with_iterable_returns_iterable(self, fresh_factory):
        result = fresh_factory.create(iterable=range(3), size=3)
        assert list(result) == [0, 1, 2]

    def test_create_specific_plugin(self, fresh_factory):
        meter = fresh_factory.create(size=10, plugin_name="tqdm")
        assert type(meter).__name__ == "TqdmProgressMeter"

    def test_create_unknown_plugin_raises(self, fresh_factory):
        with pytest.raises(ValueError, match="is not supported"):
            fresh_factory.create(size=10, plugin_name="nope")

    def test_create_plugin_unsupported_config_raises(self, fresh_factory):
        # halo cannot provide a sized BAR meter -> requesting it by name with a
        # style it cannot satisfy raises.
        style = Style(sized=[Widget.BAR])
        with pytest.raises(ValueError, match="does not support"):
            fresh_factory.create(size=10, style=style, plugin_name="halo")

    def test_create_with_style_object(self, fresh_factory):
        style = Style(sized=[Widget.BAR, Widget.ETA])
        meter = fresh_factory.create(size=10, style=style)
        assert meter is not None

    def test_create_empty_style_string_resolves_to_none(self, fresh_factory):
        # style="" is falsy, so the style resolves to None... which makes the
        # default-style lookup unnecessary. This is a documented edge: an empty
        # style name yields None and create() then fails on get_widgets. We
        # assert the AttributeError to pin the current behavior.
        fresh_factory.configure()
        with pytest.raises(AttributeError):
            fresh_factory.create(size=10, style="")

    def test_create_skips_configure_when_already_configured(
        self, fresh_factory, tmp_path
    ):
        cfg = tmp_path / "pokrok.json"
        cfg.write_text("{}")
        fresh_factory.configure(filename=str(cfg))
        assert fresh_factory.configured is True
        # second create() should not re-run configure (covers the already-
        # configured branch); a meter is still produced.
        assert fresh_factory.create(size=3) is not None

    def test_create_iterable_only_no_plugin_returns_iterable(
        self, fresh_factory, monkeypatch
    ):
        # Force no plugin available -> create() should return the raw iterable.
        fresh_factory.configure()
        monkeypatch.setattr(
            fresh_factory.plugins, "get_first_plugin", lambda *a, **k: None
        )
        result = fresh_factory.create(iterable=range(3))
        assert list(result) == [0, 1, 2]

    def test_create_no_plugin_no_iterable_returns_none(
        self, fresh_factory, monkeypatch
    ):
        fresh_factory.configure()
        monkeypatch.setattr(
            fresh_factory.plugins, "get_first_plugin", lambda *a, **k: None
        )
        assert fresh_factory.create() is None

    def test_create_triggers_configure_when_unconfigured(self, fresh_factory):
        # create() calls configure() implicitly; with no config file present
        # `configured` stays False (it only flips True when a file is loaded),
        # but plugins are loaded lazily and a meter is still produced.
        assert fresh_factory.configured is False
        assert fresh_factory.plugins.plugins is None
        meter = fresh_factory.create(size=5)
        assert meter is not None
        assert fresh_factory.plugins.plugins is not None


class TestPublicFunctions:
    def test_set_plugins_configures_singleton(self):
        pokrok.set_plugins(["tqdm"], exclusive=True)
        assert list(pokrok.FACTORY.plugins.plugins) == ["tqdm"]

    def test_set_styles_configures_singleton(self):
        pokrok.set_styles(custom=Style(widgets=["BAR"]))
        assert "custom" in pokrok.FACTORY.styles

    def test_configure_passthrough(self):
        pokrok.configure(plugin_names=["halo"], exclusive=True)
        assert list(pokrok.FACTORY.plugins.plugins) == ["halo"]

    def test_configure_with_plugin_option_kwargs(self):
        # arbitrary keyword args are forwarded to PluginManager.set_plugin_options
        # (a documented no-op placeholder); this should not raise.
        pokrok.configure(tqdm={"ncols": 80})

    def test_progress_meter_returns_meter(self):
        meter = pokrok.progress_meter(size=10)
        assert meter is not None
        assert meter.is_sized is True


class TestProgressRange:
    def test_range_with_stop(self):
        result = list(pokrok.progress_range(0, 10, 2))
        assert result == [0, 2, 4, 6, 8]

    def test_range_stop_none_uses_start_as_size(self):
        result = list(pokrok.progress_range(5))
        assert result == [0, 1, 2, 3, 4]

    def test_range_size_computed_with_step(self):
        # 0..10 step 3 -> ceil(10/3) == 4 items
        result = list(pokrok.progress_range(0, 10, 3))
        assert result == [0, 3, 6, 9]


class TestProgressIter:
    def test_none_iterable_raises(self):
        with pytest.raises(ValueError, match="Invalid iterable"):
            pokrok.progress_iter(None)

    def test_sized_iterable_infers_size(self):
        result = list(pokrok.progress_iter([1, 2, 3]))
        assert result == [1, 2, 3]

    def test_unsized_iterable_with_explicit_size(self):
        def gen():
            yield from range(3)

        result = list(pokrok.progress_iter(gen(), size=3))
        assert result == [0, 1, 2]

    def test_unsized_iterable_without_size(self):
        def gen():
            yield from range(3)

        result = list(pokrok.progress_iter(gen()))
        assert result == [0, 1, 2]


class TestProgressFile:
    def test_iterates_file_lines(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("a\nb\nc\n")
        lines = list(pokrok.progress_file(str(f), "rt"))
        assert lines == ["a\n", "b\n", "c\n"]
