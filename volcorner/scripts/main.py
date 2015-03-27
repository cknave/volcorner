#!/usr/bin/env python3
"""volcorner volume changer."""

import logging

import smokesignal

from volcorner import signals, Size
from volcorner.audio.alsa import ALSAMixer
from volcorner.config import get_config, log_level_for_verbosity, write_config
from volcorner.config.keys import CORNER, ACTIVATE_SIZE, DEACTIVATE_SIZE, VERBOSE
from volcorner.screen.x11 import RandRScreen
from volcorner.tracking import Corner
from volcorner.tracking.x11 import XInput2MouseTracker

# Amount to step the volume per scroll event
VOL_STEP = 0.05

_log = logging.getLogger("fvol")


class FVol:
    def __init__(self, config, config_path):
        """
        Initialize the app.

        :param config: the configuration from volcorner.config.get_config()
        :param config_path: the configuration file path from volcorner.config.get_config()
        """
        self.config = config
        self.config_path = config_path
        self._process_config(config)
        self.screen = None
        self._activate_region = None
        self._deactivate_region = None
        self.tracker = None
        self._in_corner = False
        self.mixer = None

        smokesignal.on(signals.ENTER_REGION, self.on_enter)
        smokesignal.on(signals.LEAVE_REGION, self.on_leave)
        smokesignal.on(signals.SCROLL_UP, self.on_scroll_up)
        smokesignal.on(signals.SCROLL_DOWN, self.on_scroll_down)
        smokesignal.on(signals.CHANGE_RESOLUTION, self.on_change_resolution)

    def run(self):
        self.mixer = ALSAMixer()
        self.mixer.open()
        _log.info("Mixer initialized")

        self.screen = RandRScreen()
        self.screen.open()
        _log.info("Screen initialized")

        self.tracker = XInput2MouseTracker()
        self._update_tracking_regions()
        self.tracker.start()
        _log.info("Tracker initialized")

        _log.info("Initialization complete; running main loop")
        # TODO: run UI main loop
        try:
            import time
            time.sleep(999999999999)
        finally:
            _log.info("Shutting down")
            self.tracker.stop()
            self.screen.close()
            self.mixer.close()

    def on_enter(self):
        """Expand the hotspot to the scroll capture region, and begin capturing scroll events."""
        self.tracker.region = self._deactivate_region
        self.tracker.grab_scroll()

    def on_leave(self):
        """Reduce the hotspot to the corner, and stop capturing scroll events."""
        self.tracker.region = self._activate_region
        self.tracker.ungrab_scroll()

    def on_scroll_up(self):
        """Increment the volume."""
        self.mixer.volume = min(1.0, self.mixer.volume + VOL_STEP)

    def on_scroll_down(self):
        """Decrement the volume."""
        self.mixer.volume = max(0.0, self.mixer.volume - VOL_STEP)

    def on_change_resolution(self, screen_size):
        self._update_tracking_regions()

    def _process_config(self, config):
        """Initialize instance variables from the config."""
        cvars = vars(config)

        corner_id = cvars[CORNER]
        self._corner = Corner.from_id(corner_id)

        activate_dim = cvars[ACTIVATE_SIZE]
        self._activate_size = Size(activate_dim, activate_dim)

        deactivate_dim = cvars[DEACTIVATE_SIZE]
        self._deactivate_size = Size(deactivate_dim, deactivate_dim)

        verbosity = cvars[VERBOSE]
        log_level = log_level_for_verbosity(verbosity)
        logging.basicConfig(level=log_level)
        _log.info("Set log level %s", logging.getLevelName(log_level))

        # Special config value: save the config now that it's set
        if cvars['save']:
            write_config(config, self.config_path)

    def _update_tracking_regions(self):
        """Update the tracking regions for the current screen resolution."""
        assert (self.screen is not None) and (self.screen.size is not None)
        assert self.tracker is not None
        # Calculate the new regions.
        self._activate_region = self._corner.rect(self.screen.size, self._activate_size)
        self._deactivate_region = self._corner.rect(self.screen.size, self._deactivate_size)
        # Track the current region.
        if not self._in_corner:
            self.tracker.region = self._activate_region
        else:
            self.tracker.region = self._deactivate_region
        _log.debug("Now tracking region %r", self.tracker.region)


def main():
    """Main function."""
    # Load configuration.
    config, config_path = get_config()
    fvol = FVol(config, config_path)
    fvol.run()

if __name__ == '__main__':
    main()
