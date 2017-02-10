"""Test utilities."""
from asyncio import Event

import asyncio
from functools import wraps
import subprocess

from nose import with_setup
import smokesignal
from xcffib.testing import XvfbTest

from volcorner.x11.x11emptyui import X11EmptyUI

# Remember the result of our xte check.
_has_xte = None


class SignalReceiver:
    """Simple signal receiver that records if it was called once."""
    def __init__(self, signal):
        self.event = Event()
        self.args = None
        self.kwargs = None
        smokesignal.on(signal, self, max_calls=1)

    def __call__(self, *args, **kwargs):
        self.event.set()
        self.args = args
        self.kwargs = kwargs

    @property
    def received(self):
        return self.event.is_set()

    def wait(self, timeout=None):
        """Wait for the signal to be received."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait_for(self.event.wait(), timeout))


def with_xvfb(f):
    """Decorator to set up and tear down an Xvfb test environment."""
    import xcffib.xproto  # Needed for an xcffib core to exist
    xvfb = XvfbTest()
    return with_setup(setup=xvfb.setUp, teardown=xvfb.tearDown)(f)


def with_ui(f):
    """Decorator to start and shut down an X11EmptyUI.

    The decorated function will receive a ui= keyword argument with the UI.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        ui = X11EmptyUI()
        ui.load()
        kwargs['ui'] = ui
        f(*args, **kwargs)
        ui.stop()
    return wrapper


def with_xte(f):
    """Decorator to verify that the xte command is available."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        global _has_xte
        if _has_xte is None:
            try:
                subprocess.check_call("xte -h >/dev/null", shell=True)
                _has_xte = True
            except (OSError, ValueError, subprocess.SubprocessError):
                _has_xte = False
        assert _has_xte, "xte is required for this test: http://hoopajoo.net/projects/xautomation.html"
        f(*args, **kwargs)
    return wrapper
