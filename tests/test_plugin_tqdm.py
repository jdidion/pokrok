"""Tests for the tqdm plugin against the real tqdm backend."""

import pokrok
from pokrok.plugins import Status
from pokrok.plugins.tqdm import TqdmProgressMeter, TqdmProgressMeterFactory
from pokrok.styles import Widget


def test_factory_name_and_superset():
    f = TqdmProgressMeterFactory()
    assert f.name == "tqdm"
    assert f.installed is True
    superset = f.style_superset.get_widgets(True)
    assert Widget.BAR in superset


def test_create_meter_and_lifecycle():
    f = TqdmProgressMeterFactory()
    meter = f.create(size=10, desc="work")
    assert isinstance(meter, TqdmProgressMeter)
    assert meter.status == Status.UNSTARTED
    meter.start()
    assert meter.status == Status.STARTED
    meter.increment(3)
    assert meter.tqdm.n == 3
    meter.finish()
    assert meter.status == Status.FINISHED


def test_increment_applies_multiplier():
    f = TqdmProgressMeterFactory()
    meter = f.create(size=100, multiplier=10)
    meter.start()
    meter.increment(2)
    assert meter.tqdm.n == 20
    meter.finish()


def test_iterate_fast_path_returns_tqdm_iterable():
    f = TqdmProgressMeterFactory()
    # multiplier None -> the optimized tqdm path is used (returns a tqdm object)
    wrapped = f.iterate(range(4), size=4, desc="d")
    assert list(wrapped) == [0, 1, 2, 3]


def test_iterate_with_multiplier_uses_base_path():
    f = TqdmProgressMeterFactory()
    # multiplier set -> falls back to BaseProgressMeterFactory.iterate (generator)
    wrapped = f.iterate(range(3), size=3, multiplier=2)
    assert list(wrapped) == [0, 1, 2]


def test_end_to_end_via_api():
    pokrok.set_plugins(["tqdm"], exclusive=True)
    result = list(pokrok.progress_iter([10, 20, 30]))
    assert result == [10, 20, 30]


def test_context_manager_via_api():
    pokrok.set_plugins(["tqdm"], exclusive=True)
    with pokrok.progress_meter(size=5) as bar:
        for _ in range(5):
            bar.increment()
    assert bar.status == Status.FINISHED
