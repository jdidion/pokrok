"""Tests for the halo plugin against the real halo backend.

Halo writes spinner frames to a stream; pytest captures stdout/stderr so the
frames do not clutter test output. We assert on the plugin's provides() logic
and meter lifecycle rather than rendered frames.
"""

import pokrok
from pokrok.plugins import Status
from pokrok.plugins.halo import HaloProgressMeter, HaloProgressMeterFactory
from pokrok.styles import Widget


def test_factory_name_and_installed():
    f = HaloProgressMeterFactory()
    assert f.name == "halo"
    assert f.installed is True


class TestProvides:
    def setup_method(self):
        self.f = HaloProgressMeterFactory()

    def test_sized_not_forced_is_false(self):
        assert self.f.provides(sized=True) is False

    def test_sized_forced_still_checks_widgets(self):
        # forced + spinner present -> True
        assert self.f.provides(sized=True, widgets=[Widget.SPINNER], force=True) is True

    def test_unsized_no_widgets_is_true(self):
        assert self.f.provides(sized=False) is True

    def test_unsized_only_spinner_strict_true(self):
        assert self.f.provides(sized=False, widgets=[Widget.SPINNER]) is True

    def test_unsized_spinner_plus_other_strict_false(self):
        assert (
            self.f.provides(sized=False, widgets=[Widget.SPINNER, Widget.BAR]) is False
        )

    def test_force_with_spinner_in_set_true(self):
        widgets = [Widget.SPINNER, Widget.BAR]
        assert self.f.provides(sized=False, widgets=widgets, force=True) is True

    def test_force_without_spinner_false(self):
        assert self.f.provides(sized=False, widgets=[Widget.BAR], force=True) is False


def test_meter_lifecycle():
    f = HaloProgressMeterFactory()
    meter = f.create(size=None, desc="loading")
    assert isinstance(meter, HaloProgressMeter)
    assert meter.status == Status.UNSTARTED
    meter.start()
    assert meter.status == Status.STARTED
    # increment is a documented no-op for a spinner
    meter.increment()
    meter.finish()
    assert meter.status == Status.FINISHED


def test_iterate_yields_all_items():
    f = HaloProgressMeterFactory()
    result = list(f.iterate(range(5), desc="spin"))
    assert result == [0, 1, 2, 3, 4]


def test_end_to_end_via_api():
    pokrok.set_plugins(["halo"], exclusive=True)
    result = list(pokrok.progress_iter(["x", "y"]))
    assert result == ["x", "y"]
