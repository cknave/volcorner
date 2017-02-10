"""Mouse tracking abstract base class."""

from abc import ABCMeta, abstractmethod
import logging

import smokesignal

from volcorner import signals

__all__ = ['MouseTracker']
_log = logging.getLogger("tracking")


class MouseTracker(metaclass=ABCMeta):
    """Mouse tracking abstract base class."""
    def __init__(self, region=None):
        """
        Initialize a MouseTracker.

        :param Rect region: The region to track
        """
        self._region = region
        self._last_point = None
        self._in_region = False

    @abstractmethod
    def start(self):
        """
        Start the mouse tracker.

        While the mouse tracker is running, it should update the :attr:`last_point` property
        with the latest mouse cursor position.
        """

    @abstractmethod
    def stop(self):
        """Stop the mouse tracker."""

    @abstractmethod
    def grab_scroll(self):
        """
        Grab the scroll wheel.

        While the scroll wheel is grabbed, the tracker should intercept scroll wheel events and
        call :meth:`on_scroll_up` and :meth:`on_scroll_down`.
        """

    @abstractmethod
    def ungrab_scroll(self):
        """Ungrab the scroll wheel."""

    @property
    def region(self):
        """Get the region of interest."""
        return self._region

    @region.setter
    def region(self, region):
        """Set the region of interest."""
        assert (region is None) or callable(region.contains)
        self._region = region
        self._update_in_region()

    @property
    def last_point(self):
        """Get the last cursor point."""
        return self._last_point

    @last_point.setter
    def last_point(self, point):
        """Set the last cursor point."""
        assert (point is None) or (hasattr(point, 'x') and hasattr(point, 'y'))
        self._last_point = point
        self._update_in_region()

    @property
    def in_region(self):
        """Check if the current cursor point is within the region of interest."""
        return self._in_region

    def on_scroll_up(self):
        """
        Subclasses should call this when the scroll wheel has been grabbed, and a scroll up event
        has occurred.
        """
        _log.debug("Scrolled up")
        smokesignal.emit(signals.SCROLL_UP)

    def on_scroll_down(self):
        """
        Subclasses should call this when the scroll wheel has been grabbed, and a scroll down
        event has occurred.
        """
        _log.debug("Scrolled down")
        smokesignal.emit(signals.SCROLL_DOWN)

    def _update_in_region(self):
        """
        Update whether the point is in the region of interest.

        If the point has moved in or out of the region, publish a notification.
        """
        was_in_region = self._in_region

        # Only test if we have both a point and a region.
        if None in (self._last_point, self._region):
            self._in_region = False
        else:
            self._in_region = self._region.contains(self._last_point)

        # Check if we entered or left the region.
        if self._in_region != was_in_region:
            _log.debug("In region: %s", self._in_region)

            # Grab the scroll wheel while inside the region.
            if self._in_region:
                smokesignal.emit(signals.ENTER_REGION)
            else:
                smokesignal.emit(signals.LEAVE_REGION)
