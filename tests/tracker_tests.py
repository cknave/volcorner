"""Abstract base mouse tracker unit tests."""

from nose import with_setup

from volcorner import signals
from volcorner.rect import Rect, Point
from volcorner.tracker import MouseTracker
from .util import SignalReceiver


tracker = None


class MockTracker(MouseTracker):
    def start(self):
        pass

    def stop(self):
        pass

    def grab_scroll(self):
        pass

    def ungrab_scroll(self):
        pass


def setup():
    global tracker
    region = Rect.make(0, 0, 10, 10)
    tracker = MockTracker(region)


@with_setup(setup)
def test_enter_region():
    """Test getting the enter signal when entering a region."""
    enter = SignalReceiver(signals.ENTER_REGION)
    tracker.last_point = Point(0, 0)
    assert enter.received


@with_setup(setup)
def test_stay_in_region():
    """Test not getting a second enter signal when staying in a region."""
    enter1 = SignalReceiver(signals.ENTER_REGION)
    tracker.last_point = Point(0, 0)
    assert enter1.received

    enter2 = SignalReceiver(signals.ENTER_REGION)
    tracker.last_point = Point(1, 1)
    assert not enter2.received


@with_setup(setup)
def test_leave_region():
    """Test getting the leave signal when leaving a region."""
    leave = SignalReceiver(signals.LEAVE_REGION)
    tracker.last_point = Point(0, 0)
    tracker.last_point = Point(10, 10)
    assert leave.received


@with_setup(setup)
def test_stay_out_of_region():
    """Test not getting the leave signal when staying out of a region."""
    leave1 = SignalReceiver(signals.LEAVE_REGION)
    tracker.last_point = Point(0, 0)
    tracker.last_point = Point(10, 10)
    assert leave1.received

    leave2 = SignalReceiver(signals.LEAVE_REGION)
    tracker.last_point = Point(11, 11)
    assert not leave2.received


@with_setup(setup)
def test_emit_scroll_up():
    """Test that the scroll signal is emitted on the scroll up event."""
    scroll_up = SignalReceiver(signals.SCROLL_UP)
    tracker.on_scroll_up()
    assert scroll_up.received


@with_setup(setup)
def test_emit_scroll_down():
    """Test that the scroll signal is emitted on the scroll down event."""
    scroll_down = SignalReceiver(signals.SCROLL_DOWN)
    tracker.on_scroll_down()
    assert scroll_down.received


@with_setup(setup)
def test_none_point():
    """Test that a None point is not in the region."""
    tracker.last_point = None
    assert not tracker.in_region


@with_setup(setup)
def test_none_region():
    """Test that a None region is not in the region."""
    tracker.region = None
    tracker.last_point = Point(1, 1)
    assert not tracker.in_region
