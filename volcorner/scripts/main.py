#!/usr/bin/env python3
"""volcorner volume changer."""

import logging
import signal

import asyncio
import smokesignal
from volcorner import signals
from volcorner.alsa.alsamixer import ALSAMixer
from volcorner.config import get_config, log_level_for_verbosity, write_config
from volcorner.config import KEY_CORNER, KEY_ACTIVATE_SIZE, KEY_DEACTIVATE_SIZE, KEY_VERBOSE
from volcorner.corner import Corner
from volcorner.qt.qtui import QtUI
from volcorner.rect import Size
from volcorner.x11.randrscreen import RandRScreen
from volcorner.x11.xinput2tracker import XInput2MouseTracker

# Amount to step the volume per scroll event
VOL_STEP = 0.05

# UI overlay size
OVERLAY_SIZE = Size(200, 200)

_log = logging.getLogger("volcorner")


class Volcorner:
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
        self.ui = None

        smokesignal.on(signals.ENTER_REGION, self.on_enter)
        smokesignal.on(signals.LEAVE_REGION, self.on_leave)
        smokesignal.on(signals.SCROLL_UP, self.on_scroll_up)
        smokesignal.on(signals.SCROLL_DOWN, self.on_scroll_down)
        smokesignal.on(signals.CHANGE_RESOLUTION, self.on_change_resolution)
        smokesignal.on(signals.CHANGE_VOLUME, self.on_change_volume)

    def run(self):
        _log.debug("Starting event loop")
        self.ui = QtUI()
        self.ui.set_event_loop()
        _log.debug("Event loop ready")

        _log.debug("Opening mixer")
        self.mixer = ALSAMixer()
        self.mixer.open()
        _log.info("Mixer ready")

        _log.debug("Opening screen")
        self.screen = RandRScreen(self.ui)
        self.screen.open()
        _log.info("Screen ready")

        _log.debug("Opening mouse tracker")
        self.tracker = XInput2MouseTracker(self.ui)
        self._update_tracking_regions()
        self.tracker.start()
        _log.info("Mouse tracker running")

        _log.debug("Loading UI")
        self.ui.corner = self._corner
        self.ui.volume = self.mixer.volume
        self._update_ui_rect()
        self.ui.load()
        _log.info("UI loaded")

        _log.info("Initialization complete; running main loop")
        try:
            # TODO: Qt never lets the python signal handler run, so we have to use SIG_DFL
            # instead of allowing the app to shut down cleanly.
            #
            # Example of doing something crazy with sockets to get around this:
            # https://github.com/sijk/qt-unix-signals
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            asyncio.get_event_loop().run_forever()
        finally:
            _log.info("Shutting down")
            self.tracker.stop()
            self.screen.close()
            self.mixer.close()

    def on_interrupt(self):
        """End the program."""
        _log.info("Received interrupt, gracefully shutting down.")
        self.ui.stop()

    def on_enter(self):
        """Expand the hotspot to the scroll capture region, and begin capturing scroll events."""
        self.tracker.region = self._deactivate_region
        self.tracker.grab_scroll()
        self.ui.show()

    def on_leave(self):
        """Reduce the hotspot to the corner, and stop capturing scroll events."""
        self.tracker.region = self._activate_region
        self.tracker.ungrab_scroll()
        self.ui.hide()

    def on_scroll_up(self):
        """Increment the volume."""
        value = min(1.0, self.mixer.volume + VOL_STEP)
        _log.info("Increasing volume to %.02f", value)
        self.mixer.volume = value

    def on_scroll_down(self):
        """Decrement the volume."""
        value = max(0.0, self.mixer.volume - VOL_STEP)
        _log.info("Decreasing volume to %.02f", value)
        self.mixer.volume = value

    def on_change_resolution(self, screen_size):
        """Update the tracking regions for the new resolution."""
        self._update_tracking_regions()
        self._update_ui_rect()

    def on_change_volume(self, volume):
        """Update the UI when the volume is changed, by this or another program."""
        self.ui.volume = volume

    def _process_config(self, config):
        """Initialize instance variables from the config."""
        cvars = vars(config)

        corner_id = cvars[KEY_CORNER]
        self._corner = Corner.from_id(corner_id)

        activate_dim = cvars[KEY_ACTIVATE_SIZE]
        self._activate_size = Size(activate_dim, activate_dim)

        deactivate_dim = cvars[KEY_DEACTIVATE_SIZE]
        self._deactivate_size = Size(deactivate_dim, deactivate_dim)

        verbosity = cvars[KEY_VERBOSE]
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

    def _update_ui_rect(self):
        """Update the display geometry for the UI overlay."""
        assert (self.screen is not None) and (self.screen.size is not None)
        assert self.ui is not None
        self.ui.overlay_rect = self._corner.rect(self.screen.size, OVERLAY_SIZE)
        _log.debug("New overlay rect %r", self.ui.overlay_rect)


def main():
    """Main function."""
    # Load configuration.
    config, config_path = get_config()
    volcorner = Volcorner(config, config_path)
    volcorner.run()

if __name__ == '__main__':
    main()
