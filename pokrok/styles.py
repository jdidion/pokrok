import enum


class Widget(enum.Enum):
    """Enumeration of widget types that are commonly supported across progress
    bar libraries.
    """

    BAR = "BAR"
    ETA = "ETA"
    ELAPSED = "ELAPSED"
    SPINNER = "SPINNER"
    COUNTER = "COUNTER"
    PERCENT = "PERCENT"


class StyleManager(dict):
    def __init__(self, default_style=None):
        super().__init__()
        self["default"] = default_style or Style()

    def set_style_options(self, config, **kwargs):
        if "styles" in config:
            for name, style_config in config["styles"].items():
                self[name] = Style(**style_config)
        if "default_style" in config:
            if isinstance(config["default_style"], str):
                self["default"] = self[config["default_style"]]
            else:
                self["default"] = Style(**config["default_style"])


class Style:
    """
    Args:
        widgets: Widgets to use for `sized` and `unsized` unless they are not
            None.
        sized: Widgets for sized progress meters.
        unsized: Widgets specifically for unsized progress meters.s
    """

    def __init__(self, widgets=None, sized=None, unsized=None):
        if widgets:
            self.sized = _resolve_widgets(sized or widgets)
            self.unsized = _resolve_widgets(unsized or widgets)
        else:
            self.sized = _resolve_widgets(sized)
            self.unsized = _resolve_widgets(unsized)

    def get_widgets(self, sized):
        return self.sized if sized else self.unsized


def _resolve_widgets(widgets):
    if widgets is None:
        return None
    return [Widget[w] if isinstance(w, str) else w for w in widgets]
