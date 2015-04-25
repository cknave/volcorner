"""ALSA unit tests."""

import os
import time

from volcorner.alsa.mixercffi import Mixer


def test_set_and_poll():
    """Test that volume is updated after a poll."""
    mixer = Mixer()
    control = mixer.find_control("Master")
    original_vol = control.get_raw_volume()
    try:
        # Set the volume to 0
        control.set_raw_volume(0)

        # Poll for an event.  It should return immediately, since we just set the volume.
        start = time.time()
        mixer.poll(timeout=500)
        end = time.time()
        assert end - start < 0.5

        # Check the volume was updated
        vol = control.get_raw_volume()
        assert vol == 0
    finally:
        # Restore original volume
        control.set_raw_volume(original_vol)


def test_poll_timeout():
    """Test that a poll times out."""
    mixer = Mixer()
    start = time.time()
    mixer.poll(timeout=500)
    end = time.time()
    assert end - start >= 0.5


def test_poll_breakfd():
    """Test that a poll can be aborted by a file descriptor."""
    mixer = Mixer()
    rfd, wfd = os.pipe()
    os.write(wfd, b'aoeu')
    start = time.time()
    mixer.poll(breakfd=rfd, timeout=500)
    end = time.time()
    assert end - start < 0.5
