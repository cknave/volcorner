"""XInput2 mouse tracker."""

import logging

import xcffib
from xcffib.xproto import ButtonPressEvent, EventMask, GeGenericEvent, GrabMode, ModMask
import xcffib.xinput
from volcorner.logging import TRACE
from volcorner.rect import Point
from volcorner.tracker import MouseTracker

__all__ = ['XInput2MouseTracker']
_log = logging.getLogger("tracking")


class XInput2MouseTracker(MouseTracker):
    """XInput mouse tracker."""
    def __init__(self, ui):
        """
        Initialize a new XInput2MouseTracker.

        :param volcorner.ui.XCBUI ui: UI to install an event handler and get XCB connection from
        """
        super().__init__()
        self._ui = ui
        self._conn = ui.xcb_connection
        self._root = None
        self._is_listening = False

    def start(self):
        self._root = self._conn.setup.roots[0].root
        self._conn.xinput = self._load_xinput()

        # Select XInput motion events.
        self._select_motion_events()

        # Listen for input events.
        self._ui.install_event_filter(self.on_event)
        self._is_listening = True

    def stop(self):
        if not self._is_listening:
            return

        self._ui.remove_event_filter(self.on_event)

    def grab_scroll(self):
        # Buttons 4 and 5 are the scroll wheel.
        self._grab_button(4)
        self._grab_button(5)
        self._conn.flush()

    def ungrab_scroll(self):
        # Buttons 4 and 5 are the scroll wheel.
        self._ungrab_button(4)
        self._ungrab_button(5)
        self._conn.flush()

    def _load_xinput(self):
        """Return the XInput extension, checking for XI2.

        Throw a ValueError if there is a problem.

        """
        xinput_major, xinput_minor = (2, 2)
        try:
            xinput = self._conn(xcffib.xinput.key)
            xinput.XIQueryVersion(xinput_major, xinput_minor).reply()
            return xinput
        except:
            _log.error("Failed to get XInput 2", exc_info=True)
            raise ValueError("XInput 2 is required.")

    def _select_motion_events(self):
        """Select raw motion events from all input devices."""
        event_mask = xcffib.xinput.EventMask.synthetic(
            deviceid=xcffib.xinput.Device.AllMaster,
            mask_len=1,
            mask=xcffib.List.synthetic(list=[xcffib.xinput.XIEventMask.RawMotion]))
        self._conn.xinput.XISelectEvents(self._root, 1, [event_mask])
        self._conn.flush()

    def _grab_button(self, button):
        """Grab press/release events for this button."""
        _log.debug("Grabbing button %s", button)
        events = EventMask.ButtonPress | EventMask.ButtonRelease
        mode = GrabMode.Async
        modifiers = ModMask.Any
        self._conn.core.GrabButton(0, self._root, events, mode, mode, 0, 0, button, modifiers)

    def _ungrab_button(self, button):
        """Ungrab all events for this button."""
        _log.debug("Ungrabbing button %s", button)
        modifiers = ModMask.Any
        self._conn.core.UngrabButton(button, self._root, modifiers)

    def on_event(self, event):
        """Handle an X event."""
        if isinstance(event, GeGenericEvent):
            # GeGenericEvent is an XInput2 pointer event.
            # Update the pointer position.
            pointer = self._conn.core.QueryPointer(self._root).reply()
            self.last_point = Point(pointer.root_x, pointer.root_y)
            _log.log(TRACE, "Pointer event %s", self._last_point)
        elif isinstance(event, ButtonPressEvent):
            # Button press is a scroll up/down event.
            _log.debug("Button press event %s", event.detail)
            if event.detail == 4:
                self.on_scroll_up()
            elif event.detail == 5:
                self.on_scroll_down()
        else:
            _log.log(TRACE, "Ignoring event %s", event)
