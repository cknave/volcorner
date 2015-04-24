"""Abstract base mixer tests."""
from volcorner import signals

from volcorner.mixer import Mixer
from tests.util import SignalReceiver


class MockMixer(Mixer):
    """Mock mixer."""
    def open(self):
        pass

    def close(self):
        pass

    @property
    def volume(self):
        return 0.0

    @volume.setter
    def volume(self, value):
        pass


def test_emit_volume_changed():
    """Test that the volume changed signal is emitted when on_volume_changed() is called."""
    mixer = MockMixer()
    volume_changed = SignalReceiver(signals.CHANGE_VOLUME)
    mixer.on_volume_changed(0.5)
    assert volume_changed.received
    assert volume_changed.args[0] == 0.5
