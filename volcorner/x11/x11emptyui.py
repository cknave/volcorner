"""X11 empty (overlayless) UI."""
import asyncio
import xcffib
from xcffib import xproto  # Required import for xcffib.connect() to work

from volcorner.ui import XCBUI


class X11EmptyUI(XCBUI):
    def __init__(self):
        super().__init__()
        self.xcb_connection = None
        self.xcb_fd = None
        self._event_filters = set()

    def load(self):
        if self.xcb_connection is None:
            self.set_event_loop()
        asyncio.get_event_loop().add_reader(self.xcb_fd, self.on_xcb_ready)

    def stop(self):
        asyncio.get_event_loop().remove_reader(self.xcb_fd)
        self.xcb_connection.disconnect()
        self.xcb_connection = None

    def install_event_filter(self, event_filter):
        self._event_filters.add(event_filter)

    def remove_event_filter(self, event_filter):
        self._event_filters.remove(event_filter)

    def show(self):
        pass  # Nothing to show

    def hide(self):
        pass  # Nothing to hide

    def set_event_loop(self):
        self.xcb_connection = xcffib.connect()
        self.xcb_fd = self.xcb_connection.get_file_descriptor()
        # Use the standard event loop

    def on_xcb_ready(self):
        while True:
            # Handle events until there are none left.
            event = self.xcb_connection.poll_for_event()
            if event is None:
                return
            # Dispatch to all event filters.
            for event_filter in self._event_filters:
                event_filter(event)
