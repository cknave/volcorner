"""ALSA mixer."""

__all__ = ['ALSAMixer']

import logging
import os
import threading

from fastvol.audio import Mixer
from . import mixercffi

_log = logging.getLogger()


class ALSAMixer(Mixer):
    """ALSA mixer."""
    def __init__(self, device="default", control="Master"):
        self._device_name = device
        self._control_name = control
        self._mixer = None
        self._control = None
        self._thread = None
        self._break_r = None
        self._break_w = None

    def open(self):
        if self._mixer is not None:
            _log.error("Tried to open already-open mixer")
            return

        # Open the mixer hardware.
        self._mixer = mixercffi.Mixer(self._device_name)
        self._control = self._mixer.find_control(self._control_name)

        # Start watching the mixer in a background thread, with a pipe to cancel it.
        self._break_r, self._break_w = os.pipe()
        self._thread = threading.Thread(
            target=self._watch_volume,
            name="ALSAMixer",
            kwargs={'breakfd': self._break_r},
            daemon=True)

    def close(self):
        if self._mixer is not None:
            _log.error("Tried to close already-closed mixer")
            return

        # Stop the watcher thread.
        os.write(self._break_w, b"1")
        os.close(self._break_w)
        self._thread.join()

        # Clean up references.
        self._mixer = None
        self._control = None
        self._thread = None
        self._break_r = None
        self._break_w = None

    @property
    def volume(self):
        assert self._control is not None

        # TODO: get for all channels
        volume = self._control.get_volume()
        return volume / 64.0

    @volume.setter
    def volume(self, value):
        assert self._control is not None

        # TODO: set for all channels
        volume = int(value * 64)
        self._control.set_volume(volume)

    def _watch_volume(self, breakfd):
        """
        Watch for changes in volume until a file descriptor is written to.

        :param int breakfd: when this file descriptor is read from, stop polling
        """
        assert self._mixer is not None

        # Loop until we read from breakfd.
        while True:
            if not self._mixer.poll(breakfd):
                break
            # Update the volume.
            self.on_volume_changed(self.volume)
        os.close(breakfd)
