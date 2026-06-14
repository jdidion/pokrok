"""Shared fixtures for the pokrok test suite.

The tests exercise the real backend libraries (tqdm, progressbar2, halo,
logging), so we keep their visible output off the terminal by redirecting the
relevant streams to dummies where it matters. tqdm/progressbar2/halo all write
to stderr by default; pytest captures that automatically, so no special
handling is required beyond not asserting on rendered output.
"""

import pytest

import pokrok


@pytest.fixture
def fresh_factory():
    """A ProgressFactory that has not yet been configured.

    Using a fresh instance per test avoids leaking plugin/style state between
    tests via the module-level singleton.
    """
    return pokrok.ProgressFactory()


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the module-level FACTORY singleton around each test.

    Several public functions (set_plugins, set_styles, configure,
    progress_*) delegate to the singleton, which caches configuration. Reset
    it so tests that touch the singleton do not depend on ordering.
    """
    pokrok.FACTORY = pokrok.ProgressFactory()
    yield
    pokrok.FACTORY = pokrok.ProgressFactory()
