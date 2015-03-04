#!/usr/bin/env python3
"""Fastvol volume changer."""

import logging

import smokesignal

from fastvol.audio.alsa import ALSAMixer
from fastvol import signals
from fastvol.tracking import Rect
from fastvol.tracking.x11 import XInput2MouseTracker

REGION_CORNER = Rect.make(0, 0, 1, 1)
REGION_SCROLL = Rect.make(0, 0, 200, 200)

# Amount to step the volume per scroll event
VOL_STEP = 0.05

logging.getLogger().setLevel(logging.DEBUG)

def main():
    """Main function."""
    # Start tracking the mouse, with the region of interest on the hot corner.
    tracker = XInput2MouseTracker()
    tracker.region = REGION_CORNER
    tracker.start()

    # Open the mixer.
    mixer = ALSAMixer()
    mixer.open()

    @smokesignal.on(signals.ENTER_REGION)
    def on_enter():
        """Expand the hotspot to the scroll capture region, and begin capturing scroll events."""
        tracker.region = REGION_SCROLL
        tracker.grab_scroll()

    @smokesignal.on(signals.LEAVE_REGION)
    def on_leave():
        """Reduce the hotspot to the corner, and stop capturing scroll events."""
        tracker.region = REGION_CORNER
        tracker.ungrab_scroll()

    @smokesignal.on(signals.SCROLL_UP)
    def on_scroll_up():
        """Increment the volume."""
        mixer.volume = min(1.0, mixer.volume + VOL_STEP)

    @smokesignal.on(signals.SCROLL_DOWN)
    def on_scroll_down():
        """Decrement the volume."""
        mixer.volume = max(0.0, mixer.volume - VOL_STEP)

    # TODO: run UI main loop
    try:
        import time
        time.sleep(999999999999)
    finally:
        tracker.stop()

if __name__ == '__main__':
    main()
