from pokrok.plugins import BaseProgressMeter, DefaultProgressMeterFactory, Status
from pokrok.styles import Style, Widget


class Progressbar2ProgressMeterFactory(DefaultProgressMeterFactory):
    def __init__(self):
        style_superset = Style(
            [
                Widget.BAR,
                Widget.ETA,
                Widget.ELAPSED,
                Widget.SPINNER,
                Widget.COUNTER,
                Widget.PERCENT,
            ]
        )
        super().__init__("progressbar", Progressbar2ProgressMeter, style_superset)

    def iterate(
        self,
        iterable,
        size=None,
        widgets=None,
        desc=None,
        start=None,
        unit=None,
        multiplier=None,
        **kwargs,
    ):
        if multiplier is None and self._load_module():
            pb = self._module.ProgressBar(
                widgets=create_widgets(self._module, widgets, desc, unit),
                initial_value=start or 0,
                max_value=size or self._module.UnknownLength,
            )
            return pb(iterable)
        else:
            return super().iterate(
                iterable, size, widgets, desc, start, unit, multiplier, **kwargs
            )


class Progressbar2ProgressMeter(BaseProgressMeter):
    def __init__(self, mod, size, widgets, desc, start, unit, multiplier, **kwargs):
        super().__init__(size)
        self.pb = mod.ProgressBar(
            widgets=create_widgets(mod, widgets, desc, unit),
            initial_value=start or 0,
            max_value=size or mod.UnknownLength,
        )
        self.multiplier = multiplier

    def start(self):
        super().start()
        self.pb.start()

    def finish(self):
        super().finish()
        self.pb.finish()

    def increment(self, n=1):
        self._check_status(Status.STARTED)
        if self.multiplier:
            n *= self.multiplier
        self.pb.update(self.pb.value + n)


PB_WIDGETS = {
    Widget.ETA: "AdaptiveETA",
    Widget.SPINNER: "AnimatedMarker",
    Widget.BAR: "Bar",
    Widget.COUNTER: "Counter",
    Widget.PERCENT: "Percentage",
    Widget.ELAPSED: "Timer",
}
"""Mapping of pokrok widget types onto progressbar2 widget classes."""


def create_widgets(mod, widgets, desc=None, unit=None):
    pb_widgets = []

    if desc:
        pb_widgets.append(desc)

    for widget in widgets or ():
        if pb_widgets:
            pb_widgets.append(" ")
        widget_class = getattr(mod, PB_WIDGETS[widget])
        pb_widgets.append(widget_class())
        if unit and widget == Widget.COUNTER:
            pb_widgets.append(" ")
            pb_widgets.append(unit)

    return pb_widgets
