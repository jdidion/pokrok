"""Tests for the logging plugin against the real stdlib logging backend.

The logging plugin builds a format-string message from the requested widgets
and emits it at a configurable interval. We attach a capturing handler to the
configured logger and assert on the emitted records, which exercises the
counter-scaling, bar, percent and interval branches.
"""

import logging

import pytest

import pokrok
from pokrok.plugins import Status
from pokrok.plugins.logging import (
    STYLE_SUPERSET,
    LoggingProgressMeter,
    LoggingProgressMeterFactory,
)
from pokrok.styles import Widget


@pytest.fixture
def capture():
    """Attach a list-capturing handler to a uniquely named logger.

    Returns a (logger_name, records) tuple. The records list collects every
    LogRecord emitted to that logger.
    """
    records = []

    class _ListHandler(logging.Handler):
        def emit(self, record):
            records.append(record)

    name = "pokrok-test-logger"
    logger = logging.getLogger(name)
    handler = _ListHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    yield name, records
    logger.removeHandler(handler)


def _make(capture, **kwargs):
    name, records = capture
    f = LoggingProgressMeterFactory()
    meter = f.create(logger_name=name, **kwargs)
    return meter, records


def test_factory_name_and_module():
    f = LoggingProgressMeterFactory()
    # the plugin name is "Logging" and the backing module is the stdlib logging
    assert f.name == "Logging"
    assert f.installed is True


def test_superset_has_sized_and_unsized():
    assert Widget.BAR in STYLE_SUPERSET.get_widgets(True)
    assert Widget.COUNTER in STYLE_SUPERSET.get_widgets(False)
    assert Widget.BAR not in STYLE_SUPERSET.get_widgets(False)


def test_lifecycle_and_finish_logs_total(capture):
    meter, records = _make(capture, size=10, interval=1)
    assert isinstance(meter, LoggingProgressMeter)
    meter.start()
    assert meter.status == Status.STARTED
    meter.increment()
    meter.finish()
    assert meter.status == Status.FINISHED
    # the finish() call logs a "Read a total of N records" summary
    assert any("Read a total of" in r.getMessage() for r in records)


def test_interval_gating_only_logs_on_crossing(capture):
    # interval 5: increments at 1..4 do not cross a multiple of 5; the 5th does.
    meter, records = _make(capture, size=100, interval=5, widgets=[Widget.COUNTER])
    meter.start()
    start_count = len(records)
    for _ in range(4):
        meter.increment()
    assert len(records) == start_count  # no crossing yet
    meter.increment()  # count now 5 -> crosses interval boundary
    assert len(records) == start_count + 1
    meter.finish()


def test_counter_unsized_format(capture):
    meter, records = _make(capture, size=None, interval=1, widgets=[Widget.COUNTER])
    meter.start()
    meter.increment()
    msg = records[-1].getMessage()
    # the counter value is scaled via float division (count / scale), so the
    # bare "{count}" format renders the float, e.g. "1.0".
    assert msg == "1.0"
    meter.finish()


def test_counter_sized_small_format(capture):
    meter, records = _make(capture, size=10, interval=1, widgets=[Widget.COUNTER])
    meter.start()
    meter.increment()
    # small size (<1000): "count/size" with no scale suffix; count is a float.
    assert records[-1].getMessage() == "1.0/10"
    meter.finish()


def test_counter_sized_large_scales_with_suffix(capture):
    # size >= 1000 triggers the k/M/... scaling branch.
    meter, records = _make(capture, size=2000, interval=1, widgets=[Widget.COUNTER])
    meter.start()
    meter.increment()
    msg = records[-1].getMessage()
    # scaled message uses 2 decimals and a 'k' suffix, e.g. "0.00/2.00k"
    assert "k" in msg
    assert "/2.00" in msg
    meter.finish()


def test_counter_with_unit(capture):
    meter, records = _make(
        capture, size=10, interval=1, widgets=[Widget.COUNTER], unit="recs"
    )
    meter.start()
    meter.increment()
    assert "recs" in records[-1].getMessage()
    meter.finish()


def test_bar_widget_renders_fill(capture):
    meter, records = _make(capture, size=10, interval=1, widgets=[Widget.BAR])
    meter.start()
    meter.increment(5)  # 50% -> 5 of 10 bar chars
    msg = records[-1].getMessage()
    assert msg.startswith("[")
    assert "*" in msg
    meter.finish()


def test_percent_widget_with_counter(capture):
    meter, records = _make(
        capture, size=10, interval=1, widgets=[Widget.COUNTER, Widget.PERCENT]
    )
    meter.start()
    meter.increment(5)
    msg = records[-1].getMessage()
    # percent is parenthesized when a counter is also present
    assert "(50%)" in msg
    meter.finish()


def test_percent_widget_without_counter(capture):
    meter, records = _make(capture, size=10, interval=1, widgets=[Widget.PERCENT])
    meter.start()
    meter.increment(3)
    msg = records[-1].getMessage()
    # bare percent (no parens) when no counter present
    assert "30%" in msg
    assert "(" not in msg
    meter.finish()


def test_elapsed_widget(capture):
    meter, records = _make(capture, size=10, interval=1, widgets=[Widget.ELAPSED])
    meter.start()
    meter.increment()
    assert "seconds" in records[-1].getMessage()
    meter.finish()


def test_unsupported_widget_filtered_out(capture):
    # SPINNER is not in the logging superset; it should be dropped silently,
    # leaving only the supported COUNTER in the message.
    meter, records = _make(
        capture, size=10, interval=1, widgets=[Widget.SPINNER, Widget.COUNTER]
    )
    meter.start()
    meter.increment()
    assert records[-1].getMessage() == "1.0/10"
    meter.finish()


def test_desc_prepended(capture):
    meter, records = _make(
        capture, size=10, interval=1, desc="loading", widgets=[Widget.COUNTER]
    )
    meter.start()
    meter.increment()
    assert records[-1].getMessage().startswith("loading ")
    meter.finish()


def test_increment_multiplier(capture):
    meter, records = _make(
        capture, size=100, interval=1, multiplier=10, widgets=[Widget.COUNTER]
    )
    meter.start()
    meter.increment(2)
    assert meter.count == 20
    meter.finish()


def test_numeric_logger_level_accepted():
    # logger_level may be passed as an int; it should be stored as-is and used
    # directly by Logger.log (covers the non-string level branch).
    f = LoggingProgressMeterFactory()
    meter = f.create(
        size=10, interval=1, logger_level=logging.DEBUG, widgets=[Widget.COUNTER]
    )
    assert meter._level == logging.DEBUG


def test_fresh_logger_gets_default_handler():
    # A logger with no pre-existing handlers gets a StreamHandler attached
    # (covers the hasHandlers() False branch).
    unique = "pokrok-fresh-logger-xyz"
    logging.getLogger(unique).handlers.clear()
    f = LoggingProgressMeterFactory()
    meter = f.create(size=10, logger_name=unique, widgets=[Widget.COUNTER])
    assert meter._logger.hasHandlers()
    # clean up to avoid leaking the handler to other tests
    meter._logger.handlers.clear()


def test_end_to_end_via_api():
    pokrok.set_plugins(["logging"], exclusive=True)
    result = list(pokrok.progress_iter([1, 2, 3, 4, 5]))
    assert result == [1, 2, 3, 4, 5]
