from pokrok.plugins import BaseProgressMeter, DefaultProgressMeterFactory
from pokrok.styles import Style, Widget


class HaloProgressMeterFactory(DefaultProgressMeterFactory):
    def __init__(self):
        style_superset = Style(unsized=[Widget.SPINNER])
        super().__init__("halo", HaloProgressMeter, style_superset)

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
        if self._load_module():
            with self._module.Halo(text=desc or ""):
                yield from iterable
        else:
            yield from iterable

    def provides(self, sized, widgets=None, force=False):
        if sized and not force:
            return False
        if widgets:
            if force:
                return Widget.SPINNER in widgets
            else:
                return len(widgets) == 1 and widgets[0] == Widget.SPINNER
        return True


class HaloProgressMeter(BaseProgressMeter):
    def __init__(self, mod, size, widgets, desc, start, unit, multiplier, **kwargs):
        super().__init__(size)
        self.spinner = mod.Halo(text=desc or "")

    def start(self):
        super().start()
        self.spinner.start()

    def finish(self):
        super().finish()
        self.spinner.succeed()

    def increment(self, n=1):
        pass
