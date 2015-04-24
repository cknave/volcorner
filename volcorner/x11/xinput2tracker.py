"""XInput2 mouse tracker."""

__all__ = ['XInput2MouseTracker']

import logging

import xcffib
from xcffib.xproto import ButtonPressEvent, EventMask, GeGenericEvent, GrabMode, ModMask
import xcffib.xinput
from volcorner.rect import Point
import volcorner.logging
from volcorner.pollthread import PollThread, run_on_thread
from volcorner.tracker import MouseTracker


_log = logging.getLogger("tracking")


class XInput2MouseTracker(MouseTracker):
    """XInput mouse tracker."""
    def __init__(self):
        super().__init__()
        self._conn = None
        self._root = None
        self._thread = None

    def start(self):
        # Connect to X server and load extensions.
        self._conn = xcffib.connect()
        self._root = self._conn.setup.roots[0].root
        self._conn.xinput = self._load_xinput()

        # Select XInput motion events.
        self._select_motion_events()

        # Process events on a background thread.
        self._thread = PollThread(
            target=self._tracker_loop,
            name="XInput2MouseTracker",
            daemon=True)
        self._thread.start()

    def stop(self):
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

    @run_on_thread('_thread')
    def grab_scroll(self):
        # Buttons 4 and 5 are the scroll wheel.
        self._grab_button(4)
        self._grab_button(5)
        self._conn.flush()

    @run_on_thread('_thread')
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

    def _tracker_loop(self):
        """Thread main loop."""
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
        if isinstance(event, GeGenericEvent):
            # GeGenericEvent is an XInput2 pointer event.
            # Update the pointer position.
            pointer = self._conn.core.QueryPointer(self._root).reply()
            self.last_point = Point(pointer.root_x, pointer.root_y)
            _log.log(volcorner.logging.TRACE, "Pointer event %s", self._last_point)
        elif isinstance(event, ButtonPressEvent):
            # Button press is a scroll up/down event.
            _log.debug("Button press event %s", event.detail)
            if event.detail == 4:
                self.on_scroll_up()
            elif event.detail == 5:
                self.on_scroll_down()
        else:
            _log.debug("Ignoring event %r", event)
