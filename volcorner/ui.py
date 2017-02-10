"""Abstract user interface."""

from abc import ABCMeta, abstractmethod

__all__ = ['UI', 'XCBUI']


class UI(metaclass=ABCMeta):
    def __init__(self):
        """Initialize the base UI."""
        self._corner = None
        self._overlay_rect = None
        self._volume = 0.0

    @abstractmethod
    def load(self):
        """Load all assets and prepare the UI."""

    @abstractmethod
    def set_event_loop(self):
        """Call asyncio.set_event_loop with the event loop for this UI."""

    @abstractmethod
    def install_event_filter(self, event_filter):
        """Install an event filter.

        :param event_filter: platform-specific event filter (e.g. QAbstractNativeEventFilter)
        """

    @abstractmethod
    def remove_event_filter(self, event_filter):
        """Remove an event filter.

        :param event_filter: event_filter that was passed to install_event_filter()
        """

    @abstractmethod
    def show(self):
        """Show the UI overlay."""

    @abstractmethod
    def hide(self):
        """Hide the UI overlay."""

    @property
    def corner(self):
        """Get the corner in which to display the UI overlay."""
        return self._corner

    @corner.setter
    def corner(self, corner):
        """Set the corner in which to display the UI overlay."""
        self._corner = corner

    @property
    def overlay_rect(self):
        """Get the rect of the overlay window."""
        return self._overlay_rect

    @overlay_rect.setter
    def overlay_rect(self, overlay_rect):
        """Set the rect of the overlay window."""
        self._overlay_rect = overlay_rect

    @property
    def volume(self):
        """Get the displayed volume level."""
        return self._volume

    @volume.setter
    def volume(self, volume):
        """Set the displayed volume level."""
        self._volume = volume


class XCBUI(UI, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.xcb_connection = None
