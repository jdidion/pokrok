"""Tests for pokrok.plugins base classes: PluginManager, provides() logic,
the ProgressMeter status state machine, and the DefaultProgressMeterFactory
module-loading behavior.

These tests use real entry points (declared in pyproject.toml) and the real
backend libraries, which are installed as dev dependencies.
"""

import pytest

from pokrok.plugins import (
    BaseProgressMeter,
    BaseProgressMeterFactory,
    DefaultProgressMeterFactory,
    PluginManager,
    ProgressMeterError,
    Status,
)
from pokrok.styles import Style, Widget


class TestPluginManagerLoad:
    def test_load_discovers_entry_points(self):
        pm = PluginManager()
        pm.load_plugins()
        # All four built-in plugins have their backends installed as dev deps.
        assert set(pm.plugins) == {"tqdm", "progressbar2", "halo", "logging"}

    def test_load_with_names_orders_listed_first(self):
        pm = PluginManager()
        pm.load_plugins(names=["halo", "tqdm"])
        names = list(pm.plugins)
        assert names[:2] == ["halo", "tqdm"]
        # non-exclusive keeps the rest too
        assert set(names) == {"tqdm", "progressbar2", "halo", "logging"}

    def test_load_exclusive_drops_unlisted(self):
        pm = PluginManager()
        pm.load_plugins(names=["tqdm"], exclusive=True)
        assert list(pm.plugins) == ["tqdm"]

    def test_load_names_ignores_unknown_name(self):
        pm = PluginManager()
        pm.load_plugins(names=["does-not-exist", "tqdm"], exclusive=True)
        assert list(pm.plugins) == ["tqdm"]

    def test_has_plugin_lazy_loads(self):
        pm = PluginManager()
        assert pm.plugins is None
        assert pm.has_plugin("tqdm") is True
        assert pm.plugins is not None

    def test_has_plugin_false_for_unknown(self):
        pm = PluginManager()
        assert pm.has_plugin("nope") is False

    def test_get_plugin_returns_instance(self):
        pm = PluginManager()
        pm.load_plugins()
        plugin = pm.get_plugin("tqdm")
        assert plugin.name == "tqdm"

    def test_get_plugin_unknown_raises(self):
        pm = PluginManager()
        pm.load_plugins()
        with pytest.raises(ValueError, match="No such plugin"):
            pm.get_plugin("nope")

    def test_set_plugin_options_is_noop(self):
        # documented placeholder; should not raise
        pm = PluginManager()
        pm.set_plugin_options({"anything": 1}, foo="bar")


class TestGetFirstPlugin:
    def test_empty_plugins_returns_none(self):
        pm = PluginManager()
        pm.plugins = {}  # simulate "loaded, none installed"
        assert pm.get_first_plugin(sized=True, widgets=[Widget.BAR]) is None

    def test_no_constraints_returns_first(self):
        pm = PluginManager()
        pm.load_plugins(names=["tqdm"], exclusive=True)
        assert pm.get_first_plugin().name == "tqdm"

    def test_lazy_loads_when_none(self):
        pm = PluginManager()
        assert pm.plugins is None
        plugin = pm.get_first_plugin()
        assert plugin is not None

    def test_strict_match_selects_capable_plugin(self):
        pm = PluginManager()
        # halo only provides SPINNER and only for unsized; tqdm provides BAR.
        pm.load_plugins(names=["halo", "tqdm"])
        plugin = pm.get_first_plugin(sized=True, widgets=[Widget.BAR])
        # halo cannot provide a sized BAR, so tqdm should be chosen.
        assert plugin.name == "tqdm"

    def test_force_fallback_when_no_strict_match(self):
        pm = PluginManager()
        # Request a widget that no plugin provides strictly in its superset for
        # this configuration, forcing the force=True second pass.
        pm.load_plugins(names=["halo"], exclusive=True)
        # halo strictly only supports unsized SPINNER. Ask for unsized SPINNER
        # plus a counter -> not a strict subset, should fall through to force.
        plugin = pm.get_first_plugin(
            sized=False, widgets=[Widget.SPINNER, Widget.COUNTER]
        )
        assert plugin is not None
        assert plugin.name == "halo"


class _SupersetFactory(BaseProgressMeterFactory):
    """Minimal concrete factory to exercise BaseProgressMeterFactory.provides."""

    def __init__(self, superset):
        self._superset = superset

    @property
    def name(self):
        return "test"

    @property
    def installed(self):
        return True

    @property
    def style_superset(self):
        return self._superset

    def create(self, *args, **kwargs):  # pragma: no cover - not exercised here
        return None


class TestProvides:
    def test_no_widgets_requested_returns_true(self):
        f = _SupersetFactory(Style(sized=[Widget.BAR]))
        assert f.provides(sized=True, widgets=None) is True

    def test_no_superset_returns_true(self):
        f = _SupersetFactory(None)
        assert f.provides(sized=True, widgets=[Widget.BAR]) is True

    def test_superset_with_no_widgets_for_dimension_returns_false(self):
        # superset has sized widgets but none for unsized
        f = _SupersetFactory(Style(sized=[Widget.BAR]))
        assert f.provides(sized=False, widgets=[Widget.SPINNER]) is False

    def test_strict_requires_all_widgets_in_superset(self):
        f = _SupersetFactory(Style(sized=[Widget.BAR, Widget.ETA]))
        assert f.provides(sized=True, widgets=[Widget.BAR]) is True
        assert f.provides(sized=True, widgets=[Widget.BAR, Widget.SPINNER]) is False

    def test_force_requires_any_overlap(self):
        f = _SupersetFactory(Style(sized=[Widget.BAR]))
        # BAR overlaps -> force True
        assert f.provides(sized=True, widgets=[Widget.BAR, Widget.SPINNER], force=True)
        # no overlap -> force still False
        assert not f.provides(sized=True, widgets=[Widget.SPINNER], force=True)


class TestDefaultFactoryModuleLoading:
    def test_installed_true_for_real_module(self):
        f = DefaultProgressMeterFactory("tqdm", object, None)
        assert f.installed is True

    def test_installed_false_for_missing_module(self):
        f = DefaultProgressMeterFactory(
            "no-such-pkg", object, None, module_name="definitely_not_installed_xyz"
        )
        assert f.installed is False

    def test_create_returns_none_when_module_missing(self):
        f = DefaultProgressMeterFactory(
            "no-such-pkg", object, None, module_name="definitely_not_installed_xyz"
        )
        assert f.create(size=10) is None

    def test_name_property(self):
        f = DefaultProgressMeterFactory("foo", object, None)
        assert f.name == "foo"


class _Meter(BaseProgressMeter):
    """Concrete BaseProgressMeter for exercising the status state machine."""

    def increment(self, n=1):
        self._check_status(Status.STARTED)
        return n


class TestStatusStateMachine:
    def test_initial_status_unstarted(self):
        m = _Meter(size=10)
        assert m.status == Status.UNSTARTED
        assert m.is_sized is True

    def test_unsized_when_no_size(self):
        assert _Meter().is_sized is False

    def test_start_transitions_to_started(self):
        m = _Meter()
        m.start()
        assert m.status == Status.STARTED

    def test_finish_transitions_to_finished(self):
        m = _Meter()
        m.start()
        m.finish()
        assert m.status == Status.FINISHED

    def test_start_twice_raises(self):
        m = _Meter()
        m.start()
        with pytest.raises(ProgressMeterError):
            m.start()

    def test_finish_before_start_raises(self):
        m = _Meter()
        with pytest.raises(ProgressMeterError):
            m.finish()

    def test_increment_before_start_raises(self):
        m = _Meter()
        with pytest.raises(ProgressMeterError):
            m.increment()

    def test_check_status_error_false_returns_bool(self):
        m = _Meter()
        assert m._check_status(Status.STARTED, error=False) is False
        m.start()
        assert m._check_status(Status.STARTED, error=False) is True

    def test_context_manager_drives_status(self):
        m = _Meter()
        with m as entered:
            assert entered is m
            assert m.status == Status.STARTED
        assert m.status == Status.FINISHED


class TestBaseFactoryIterate:
    def test_iterate_yields_items_and_increments(self):
        """BaseProgressMeterFactory.iterate wraps create() in a context manager.

        We drive it through the logging plugin's factory (a BaseProgressMeter
        backend) and confirm every item is yielded.
        """
        from pokrok.plugins.logging import LoggingProgressMeterFactory

        f = LoggingProgressMeterFactory()
        items = list(f.iterate(range(5), size=5))
        assert items == [0, 1, 2, 3, 4]

    def test_iterate_returns_raw_iterable_when_create_returns_none(self, monkeypatch):
        """When create() yields no meter, iterate falls back to the raw iterable."""
        from pokrok.plugins.logging import LoggingProgressMeterFactory

        f = LoggingProgressMeterFactory()
        monkeypatch.setattr(f, "create", lambda *a, **k: None)
        # iterate() is a generator; with no meter it yields the source items
        # through unchanged.
        assert list(f.iterate([1, 2, 3], size=3)) == [1, 2, 3]
