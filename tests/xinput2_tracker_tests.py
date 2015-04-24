"""XInput2MouseTracker tests."""

import subprocess

from volcorner.rect import Rect
from volcorner import signals
from volcorner.x11.xinput2tracker import XInput2MouseTracker
from .util import SignalReceiver, with_xte, with_xvfb

TEST_AREA = Rect.make(64, 64, 1, 1)


@with_xvfb
@with_xte
def test_mouse_tracking():
    # Track the test region.
    tracker = XInput2MouseTracker()
    tracker.region = TEST_AREA
    tracker.start()
    try:
        # Move the mouse into the region, expecting the enter event.
        enter = SignalReceiver(signals.ENTER_REGION)
        subprocess.check_call(['xte', 'mousemove 64 64'])
        enter.wait(0.5)
        assert enter.received

        # Move the mouse out of the region, expecting the leave event.
        leave = SignalReceiver(signals.LEAVE_REGION)
        subprocess.check_call(['xte', 'mousemove 65 65'])
        leave.wait(0.5)
        assert leave.received
    finally:
        tracker.stop()


@with_xvfb
@with_xte
def test_scroll_grab():
    tracker = XInput2MouseTracker()
    tracker.start()
    try:
        tracker.grab_scroll()
        subprocess.check_call(['xte', 'mousemove 0 0'])  # Wait a bit for the grab to finish by moving the mouse

        # Test the scroll up event.
        scroll_up = SignalReceiver(signals.SCROLL_UP)
        subprocess.check_call(['xte', 'mouseclick 4', 'mousemove 0 0'])  # seem to need mousemove to trigger the event?
        scroll_up.wait(0.5)
        assert scroll_up.received

        # Test the scroll down event.
        scroll_down = SignalReceiver(signals.SCROLL_DOWN)
        subprocess.check_call(['xte', 'mouseclick 5', 'mousemove 0 0'])
        scroll_down.wait(0.5)
        assert scroll_down.received
    finally:
        tracker.stop()
