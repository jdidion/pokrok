from pokrok.plugins import BaseProgressMeter, DefaultProgressMeterFactory, Status
from pokrok.styles import Style, Widget


class TqdmProgressMeterFactory(DefaultProgressMeterFactory):
    def __init__(self):
        style_superset = Style([Widget.BAR, Widget.ETA, Widget.ELAPSED, Widget.SPINNER])
        super().__init__("tqdm", TqdmProgressMeter, style_superset)

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
            return self._module.tqdm(
                iterable,
                total=size,
                desc=desc,
                initial=start or 0,
                unit_scale=True,
                unit=unit or "it",
            )
        else:
            return super().iterate(
                iterable, size, widgets, desc, start, unit, multiplier
            )


class TqdmProgressMeter(BaseProgressMeter):
    def __init__(
        self,
        mod,
        size,
        widgets,
        desc,
        start,
        unit,
        multiplier,
        unit_scale=True,
        **kwargs,
    ):
        super().__init__(size)
        self.tqdm = mod.tqdm(
            total=size,
            desc=desc,
            initial=start or 0,
            unit_scale=unit_scale,
            unit=unit or "it",
        )
        self.multiplier = multiplier

    def finish(self):
        super().finish()
        self.tqdm.close()

    def increment(self, n=1):
        self._check_status(Status.STARTED)
        if self.multiplier:
            n *= self.multiplier
        self.tqdm.update(n)
