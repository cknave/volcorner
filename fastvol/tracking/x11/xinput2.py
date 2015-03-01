"""XInput2 mouse tracker."""

__all__ = ['XInput2MouseTracker']

import logging
import os
import select
import threading

import xcffib
from xcffib.xproto import ButtonMask, ButtonPressEvent, EventMask, GeGenericEvent, GrabMode
import xcffib.xinput

from fastvol.tracking import MouseTracker, Point


log = logging.getLogger()


class XInput2MouseTracker(MouseTracker):
    """XInput mouse tracker."""
    def __init__(self):
        super().__init__()
        self.conn = None
        self.root = None
        self.break_r = None
        self.break_w = None
        self.thread = None

    def start(self):
        # Connect to X server and load extensions.
        self.conn = xcffib.connect()
        self.root = self.conn.setup.roots[0].root
        self.conn.xinput = self._load_xinput()

        # Select XInput motion events.
        self._select_motion_events()

        # Process events on a background thread.
        self.break_r, self.break_w = os.pipe()
        self.thread = threading.Thread(
            target=self._get_events,
            kwargs={'breakfd': self.break_r},
            name="XInput2MouseTracker",
            daemon=True)
        self.thread.start()

    def stop(self):
        # Do nothing if already stopped.
        if self.thread is None:
            return

        # Wake up the background thread by writing to its break pipe.
        os.write(self.break_w, b"1")
        os.close(self.break_w)
        self.break_w = None

        # Wait for the thread to finish.
        self.thread.join()
        self.thread = None

        # Close the read end of the break pipe.
        os.close(self.break_r)
        self.break_r = None

        # Close the X connection.
        self.root = None
        self.conn.disconnect()
        self.conn = None

    def grab_scroll(self):
        # Buttons 4 and 5 are the scroll wheel.
        self._grab_button(4)
        self._grab_button(5)

    def ungrab_scroll(self):
        # Buttons 4 and 5 are the scroll wheel.
        self._ungrab_button(4)
        self._ungrab_button(5)

    def _load_xinput(self):
        """Return the XInput extension, checking for XI2.

        Throw a ValueError if there is a problem.

        """
        xinput_major, xinput_minor = (2, 2)
        try:
            xinput = self.conn(xcffib.xinput.key)
            xinput.XIQueryVersion(xinput_major, xinput_minor).reply()
            return xinput
        except:
            log.error("Failed to get XInput 2", exc_info=True)
            raise ValueError("XInput 2 is required.")

    def _select_motion_events(self):
        """Select raw motion events from all input devices."""
        event_mask = xcffib.xinput.EventMask.synthetic(
            deviceid=xcffib.xinput.Device.AllMaster,
            mask_len=1,
            mask=xcffib.List.synthetic(list=[xcffib.xinput.XIEventMask.RawMotion]))
        self.conn.xinput.XISelectEvents(self.root, 1, [event_mask])
        self.conn.flush()

    def _grab_button(self, button):
        """Grab press/release events for this button."""
        events = EventMask.ButtonPress | EventMask.ButtonRelease
        mode = GrabMode.Async
        self.conn.core.GrabButton(0, self.root, events, mode, mode, 0, 0, button, 0)

    def _ungrab_button(self, button):
        """Ungrab all events for this button."""
        self.conn.core.UngrabButton(button, self.root, 0)

    def _get_events(self, breakfd=None):
        # Prepare to poll for events.
        poll = select.poll()
        poll.register(self.conn.get_file_descriptor(), select.POLLIN)
        if breakfd is not None:
            poll.register(breakfd, select.POLLIN)

        # Loop until breakfd is written to.
        while True:
            fds = [fd for (fd, event) in poll.poll()]
            if breakfd in fds:
                break

            # Handle all available X events.
            while True:
                event = self.conn.poll_for_event()
                if event is None:
                    break
                self._handle_event(event)

    def _handle_event(self, event):
        """Handle an X event."""
        if isinstance(event, xcffib.xproto.GeGenericEvent):
            # GeGenericEvent is an XInput2 pointer event.
            # Update the pointer position.
            pointer = self.conn.core.QueryPointer(self.root).reply()
            self.last_point = Point(pointer.root_x, pointer.root_y)
        elif isinstance(event, ButtonPressEvent):
            # Button press is a scroll up/down event.
            if event.detail == 4:
                self.on_scroll_up()
            elif event.detail == 5:
                self.on_scroll_down()
