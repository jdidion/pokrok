"""Main pokrok API.

All functions support the following basic keyword arguments. Additional keyword
arguments can be passed to whichever plugin is selected, and that plugin can
choose whether or not to use those arguments.

* start: The starting value of the progress counter. Only value if `size` is
  also specified.
* size: The total size (i.e. max counter value) of the progress bar.
* style: The desired style; a string name of a pre-defined style, or a Style
  object.
* desc: A string description to display next to the progress bar.
* plugin_name: Name of a specific plugin to use.

"""
from collections.abc import Sized
try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources
import json
import math
import os

import pokrok.plugins
import pokrok.styles
from pokrok.styles import Style, Widget

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


class ProgressFactory:
    def __init__(self):
        self.plugins = pokrok.plugins.PluginManager()
        self.styles = pokrok.styles.StyleManager()
        self.configured = False

    @property
    def default_paths(self):
        return [
            os.path.join(path, 'pokrok.json')
            for path in (
                os.getcwd(),
                os.path.abspath(os.path.expanduser('~')))
        ]

    def configure(
            self, filename=None, plugin_names=None, exclusive=False,
            styles=None, **kwargs):
        if not (filename or self.configured):
            for fname in self.default_paths:
                if os.path.exists(fname):
                    filename = fname
                    break

        if filename:
            config = None
            if os.path.exists(filename):
                with open(filename, 'rt') as inp:
                    config = json.load(inp)
            else:
                try:
                    package, path = filename.split(':')
                    if importlib_resources.is_resource(package, path):
                        config = json.loads(
                            importlib_resources.read_text(package, path)
                        )
                except:
                    pass
            if config is None:
                raise ValueError("File not found: {}".format(filename))
            self.plugins.set_plugin_options(config)
            self.styles.set_style_options(config)
            self.configured = True

        if plugin_names:
            self.plugins.load_plugins(plugin_names, exclusive)
        if kwargs:
            self.plugins.set_plugin_options(**kwargs)
        if styles:
            self.styles.update(**styles)

    def create(
            self, iterable=None, size=None, style='default', plugin_name=None,
            **kwargs):
        """Create a progress meter. All parameters are optional. The default
        behavior (i.e. when just calling `create()`) is to return an unsized
        ProgressMeter with default style.

        Args:
            iterable: An iterable to wrap.
            size: The size of the progress meter, or None for an unsized
                progress meter.
            style: The desired style.
            plugin_name: The name of a specific plugin to use.
            kwargs: Additional keyword arguments to pass to the plugin creation method.

        Returns:
            A ProgressMeter if `iterable` is None, otherwise an iterable, or
            None if a ProgressMeter could not be created.

        Raises:
            ProgressMeterError if a specific plugin is requested and is not
            available or does not support the requested configuration.
        """
        if not self.configured:
            self.configure()

        if isinstance(style, str):
            style = self.styles[style] if style else None

        sized = size is not None
        widgets = style.get_widgets(sized)

        if plugin_name:
            if not self.plugins.has_plugin(plugin_name):
                raise ValueError(
                    "Plugin {} is not supported".format(plugin_name))
            plugin = self.plugins.get_plugin(plugin_name)
            if not plugin.provides(sized, widgets, force=True):
                raise ValueError(
                    "Plugin {} does not support the requested configuration "
                    "(sized={}, style={})".format(plugin_name, sized, widgets))
        else:
            plugin = self.plugins.get_first_plugin(sized, widgets)

        if plugin and iterable:
            return plugin.iterate(
                iterable, size=size, widgets=widgets, **kwargs)
        elif plugin:
            return plugin.create(size=size, widgets=widgets, **kwargs)
        elif iterable:
            return iterable
        else:
            return None


# Singleton factory class
FACTORY = ProgressFactory()


def set_plugins(names, exclusive=False):
    """High-level configuration of progress meter packages.

    Args:
        names: Names of plugins to prefer, in order.
        exclusive: Whether the listed packages should be the only ones allowed.
    """
    FACTORY.configure(plugin_names=names, exclusive=exclusive)


def set_styles(**styles):
    """Convenience method for configuring progress meter styles.

    Args:
        styles: keyword arguments, where the name is the style name and the
            value is a pokrok.styles.Style object.
    """
    FACTORY.configure(styles=styles)


def configure(**kwargs):
    """Low-level configuration. This is just a pass-through to
    FACTORY.configure().

    Args:
        kwargs: Keyword arguments to pass to FACTORY.configure().
    """
    FACTORY.configure(**kwargs)


def progress_range(start, stop=None, step=1, **kwargs):
    """Iterate over a range while showing a progress bar.

    Args:
        start: Range start.
        stop: Range stop.
        step: Range step.
        kwargs: Additional arguments - see package documentation.

    Returns:
        An iterable.
    """
    if stop is not None:
        r = range(start, stop, step)
        size = math.ceil((stop - start) / step)
    else:
        r = range(start)
        size = start
    return progress_iter(r, size=size, **kwargs)


def progress_file(filename, mode, **kwargs):
    """Iterate over a file while showing a progress bar.

    Args:
        filename: The name of the file to open and iterate over.
        mode: The file mode (must be readable).
        kwargs: Additional arguments - see package documentation.

    Yields:
        Lines from the file.
    """
    with open(filename, mode) as f:
        yield from progress_iter(f, **kwargs)


def progress_iter(iterable, size=None, **kwargs):
    """Wrap an iterable in a progress bar.

    Args:
        iterable: The iterable to wrap.
        size: The number of items that will be iterated over by the iterable.
            If None and this iterable happens to be Sized, the size will be
            determined using `len`.
        kwargs: Additional arguments - see package documentation.

    Returns:
        An iterable.
    """
    if iterable is None:
        raise ValueError("Invalid iterable")
    if size is None and isinstance(iterable, Sized):
        size = len(iterable)
    return FACTORY.create(iterable=iterable, size=size, **kwargs)


def progress_meter(**kwargs):
    """
    Create a progress meter.

    Args:
        kwargs: see package documentation.

    Returns:
        A ProgressMeter.
    """
    return FACTORY.create(**kwargs)
