"""Tests for the progressbar2 plugin against the real progressbar backend."""

import progressbar

import pokrok
from pokrok.plugins import Status
from pokrok.plugins.progressbar2 import (
    PB_WIDGETS,
    Progressbar2ProgressMeter,
    Progressbar2ProgressMeterFactory,
    create_widgets,
)
from pokrok.styles import Widget


def test_factory_name_and_superset():
    f = Progressbar2ProgressMeterFactory()
    # backend module name is "progressbar"
    assert f._package == "progressbar"
    assert f.installed is True
    superset = f.style_superset.get_widgets(True)
    assert Widget.COUNTER in superset
    assert Widget.PERCENT in superset


def test_create_widgets_maps_every_pokrok_widget():
    widgets = list(PB_WIDGETS.keys())
    pb_widgets = create_widgets(progressbar, widgets, desc="task", unit="recs")
    # description prepended
    assert pb_widgets[0] == "task"
    # all mapped widget classes are real progressbar widget instances
    classes = {type(w).__name__ for w in pb_widgets if not isinstance(w, str)}
    assert "Bar" in classes
    assert "Counter" in classes
    assert "Percentage" in classes


def test_create_widgets_unit_only_after_counter():
    pb_widgets = create_widgets(progressbar, [Widget.COUNTER], unit="bytes")
    # unit string follows the counter
    assert "bytes" in pb_widgets


def test_create_widgets_no_desc_no_leading_space():
    pb_widgets = create_widgets(progressbar, [Widget.BAR])
    # first element should be the Bar widget, not a separator space
    assert not (isinstance(pb_widgets[0], str) and pb_widgets[0] == " ")


def test_meter_lifecycle_sized():
    f = Progressbar2ProgressMeterFactory()
    meter = f.create(size=10, widgets=[Widget.BAR, Widget.PERCENT])
    assert isinstance(meter, Progressbar2ProgressMeter)
    meter.start()
    assert meter.status == Status.STARTED
    meter.increment(4)
    assert meter.pb.value == 4
    meter.finish()
    assert meter.status == Status.FINISHED


def test_increment_applies_multiplier():
    f = Progressbar2ProgressMeterFactory()
    meter = f.create(size=100, widgets=[Widget.BAR], multiplier=5)
    meter.start()
    meter.increment(2)
    assert meter.pb.value == 10
    meter.finish()


def test_unsized_uses_unknown_length():
    f = Progressbar2ProgressMeterFactory()
    meter = f.create(size=None, widgets=[Widget.SPINNER])
    # max_value should be UnknownLength sentinel for unsized meters
    assert meter.pb.max_value is progressbar.UnknownLength


def test_iterate_fast_path():
    f = Progressbar2ProgressMeterFactory()
    wrapped = f.iterate(range(4), size=4, widgets=[Widget.BAR])
    assert list(wrapped) == [0, 1, 2, 3]


def test_end_to_end_via_api():
    pokrok.set_plugins(["progressbar2"], exclusive=True)
    result = list(pokrok.progress_iter([1, 2, 3]))
    assert result == [1, 2, 3]
