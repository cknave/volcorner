"""XRandR screen monitor."""

import logging

import xcffib
import xcffib.xproto
import xcffib.randr
from xcffib.randr import ScreenChangeNotifyEvent
from volcorner.rect import Size
from volcorner.screen import Screen

__all__ = ['RandRScreen']
_log = logging.getLogger("screen")


class RandRScreen(Screen):
    def __init__(self, ui):
        """Initialize a new RandRScreen.

        The given UI will be used for its xcb_connection to load the RandR extension,   

        :param volcorner.ui.XCBUI ui: UI to attach to
        """
        self._ui = ui
        self._conn = ui.xcb_connection
        self._root = None
        self._size = None
        self._opened_connection = False
        self._listening = False

    def open(self):
        # Connect to X server and load extensions.
        self._root = self._conn.setup.roots[0].root
        self._conn.randr = self._load_randr()

        # Select screen change events.
        self._select_screen_change_events()

        # Update the current size.
        screen = self._conn.setup.roots[0]
        self._size = Size(screen.width_in_pixels, screen.height_in_pixels)

        # Listen for events.
        self._ui.install_event_filter(self.handle_event)
        self._listening = True

    def close(self):
        # Do nothing if already stopped.
        if not self._listening:
            return

        self._root = None
        self._size = None
        self._listening = False

    @property
    def size(self):
        return self._size

    def _load_randr(self):
        """
        Load the RandR extension, checking for RandR 1.4.

        Throw a ValueError if there is a problem.

        :return: the RandR extension object
        """
        randr_major, randr_minor = (1, 4)
        try:
            randr = self._conn(xcffib.randr.key)
            randr.QueryVersion(randr_major, randr_minor).reply()
            return randr
        except:
            _log.error("Failed to get RandR", exc_info=True)
            raise ValueError("RandR is required.")

    def _select_screen_change_events(self):
        """Select screen change events."""
        self._conn.randr.SelectInput(self._root, xcffib.randr.NotifyMask.ScreenChange)
        self._conn.flush()

    def handle_event(self, event):
        """Handle an X event."""
        if isinstance(event, ScreenChangeNotifyEvent):
            self._size = Size(event.width, event.height)
            self.on_resolution_changed(self._size)
