"""XRandR screen monitor."""

__all__ = ['RandRScreen']

import logging

import xcffib
import xcffib.xproto
import xcffib.randr
from xcffib.randr import ScreenChangeNotifyEvent
from volcorner.rect import Size
from volcorner.screen import Screen
from volcorner.pollthread import PollThread

_log = logging.getLogger("screen")


class RandRScreen(Screen):
    def __init__(self):
        self._conn = None
        self._root = None
        self._size = None
        self._thread = None

    def open(self):
        # Connect to X server and load extensions.
        self._conn = xcffib.connect()
        self._root = self._conn.setup.roots[0].root
        self._conn.randr = self._load_randr()

        # Select screen change events.
        self._select_screen_change_events()

        # Update the current size.
        screen = self._conn.setup.roots[0]
        self._size = Size(screen.width_in_pixels, screen.height_in_pixels)

        # Process events on a background thread.
        self._thread = PollThread(
            target=self._monitor_loop,
            name="RandRScreen",
            daemon=True)
        self._thread.start()

    def close(self):
        # Do nothing if already stopped.
        if self._thread is None:
            return

        # Wait for the thread to finish.
        self._thread.stop()
        self._thread = None

        # Close the X connection.
        self._root = None
        self._conn.disconnect()
        self._conn = None
        self._size = None

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

    def _monitor_loop(self):
        fd = self._conn.get_file_descriptor()
        self._thread.poll(lambda _: self._handle_all_events(), fd)

    def _handle_all_events(self):
        """Handle all available X events."""
        while True:
            event = self._conn.poll_for_event()
            if event is None:
                break
            self._handle_event(event)

    def _handle_event(self, event):
        """Handle an X event."""
        if isinstance(event, ScreenChangeNotifyEvent):
            self._size = Size(event.width, event.height)
            self.on_resolution_changed(self._size)
