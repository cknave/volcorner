"""ALSA mixer."""
import asyncio

import logging
import math

from volcorner.mixer import Mixer
from . import mixercffi

__all__ = ['ALSAMixer']
_log = logging.getLogger("audio")

# ALSA Rounding direction parameter (0=exact)
ROUND_DIR = 0


class ALSAMixer(Mixer):
    """ALSA mixer."""
    def __init__(self, device="default", control="Master"):
        self._device_name = device
        self._control_name = control
        self._mixer = None
        self._control = None
        self._supports_db = False
        self._listening_fds = []

    def open(self):
        if self._mixer is not None:
            _log.error("Tried to open already-open mixer")
            return

        # Open the mixer hardware.
        self._mixer = mixercffi.Mixer(self._device_name)
        self._control = self._mixer.find_control(self._control_name)

        # Check if the hardware supports decibels.
        try:
            min, max = self._control.get_db_range()
            self._supports_db = (min < max)
        except mixercffi.ALSAMixerError:
            self._supports_db = False

        # Listen for mixer updates.
        for fd in self._mixer.get_poll_fds():
            asyncio.get_event_loop().add_reader(fd, self.on_mixer_ready)

    def close(self):
        if self._mixer is None:
            _log.error("Tried to close already-closed mixer")
            return

        for fd in self._listening_fds:
            asyncio.get_event_loop().remove_reader(fd)

    @property
    def volume(self):
        assert self._control is not None
        if self._supports_db:
            min, max = self._control.get_db_range()
            value = self._control.get_db()

            if use_linear_db_scale(min, max):
                return (value - min) / float(max - min)

            normalized = exp10((value - max) / 6000.0)
            if min != SND_CTL_TLV_DB_GAIN_MUTE:
                min_norm = exp10((min - max) / 6000.0)
                normalized = (normalized - min_norm) / (1 - min_norm)
            return normalized
        else:  # No dB support
            min, max = self._control.get_raw_range()
            if min == max:
                raise mixercffi.ALSAMixerError(message="Unable to determine volume range")

            value = self._control.get_raw_volume()
            return (value - min) / float(max - min)

    @volume.setter
    def volume(self, value):
        assert self._control is not None
        assert 0.0 <= value <= 1.0
        if self._supports_db:
            min, max = self._control.get_db_range()

            if use_linear_db_scale(min, max):
                db = round_dir(value * (max - min), ROUND_DIR) + min
                _log.debug("Setting %.02f dB", db / 100.0)
                self._control.set_db(db)
            else:
                if min != SND_CTL_TLV_DB_GAIN_MUTE:
                    min_norm = exp10((min - max) / 6000.0)
                    value = value * (1 - min_norm) + min_norm
                db = round_dir(6000.0 * math.log10(value), ROUND_DIR)
                _log.debug("Setting %.02f dB", db / 100.0)
                self._control.set_db(db)
        else:  # No dB support
            min, max = self._control.get_raw_range()
            if min == max:
                raise mixercffi.ALSAMixerError(message="Unable to determine volume range")
            volume = int(value * (max - min) + min)
            _log.debug("Setting %d hw volume", volume)
            self._control.set_raw_volume(volume)

    def on_mixer_ready(self):
        assert self._mixer is not None
        _log.debug("Mixer is ready, handling events.")
        self._mixer.handle_events()
        _log.debug("Finished handling mixer events.")
        self.on_volume_changed(self.volume)


#
# Functions from volume_mapping.c in alsa-utils:
#

MAX_LINEAR_DB_SCALE = 24
SND_CTL_TLV_DB_GAIN_MUTE = -9999999


def use_linear_db_scale(min_db, max_db):
    return max_db - min_db <= MAX_LINEAR_DB_SCALE * 100


def exp10(x):
    return math.exp(x * math.log(10))


def round_dir(x, dir):
    if dir > 0:
        return round(math.ceil(x))
    elif dir < 0:
        return round(math.floor(x))
    else:
        return round(x)
