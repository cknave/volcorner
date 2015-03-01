"""Mouse tracking abstract base class."""

__all__ = ['MouseTracker']

from abc import ABCMeta, abstractmethod

class MouseTracker():
    """Abstract mouse tracker."""
    __metaclass__ = ABCMeta

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
        """Start the mouse tracker."""

    @abstractmethod
    def stop(self):
        """Stop the mouse tracker."""

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

        if self._in_region != was_in_region:
            print("Tracker: {}".format(self._in_region))
            # TODO: publish notification
