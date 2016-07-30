"""Abstract base class for screen info."""

import smokesignal

from abc import ABCMeta, abstractmethod
from volcorner import signals


class Screen(metaclass=ABCMeta):
    """Abstract base class for screen info."""
    @abstractmethod
    def open(self):
        """
        Start monitoring the screen resolution for changes.

        When the resolution is changed, call on_resolution_changed.
        """

    @abstractmethod
    def close(self):
        """Stop monitoring the screen resolution for changes."""

    @property
    @abstractmethod
    def size(self):
        """
        Return the current size of the screen.
        :return: the screen size
        :rtype: Size
        """

    def on_resolution_changed(self, size):
        """
        Called by the subclass when the screen resolution has changed.

        :param Size size: the new resolution
        """
        smokesignal.emit(signals.CHANGE_RESOLUTION, size)
