"""Abstract base audio mixer."""

__all__ = ['Mixer']

from abc import ABCMeta, abstractmethod
import smokesignal

from volcorner import signals


class Mixer(metaclass=ABCMeta):
    @abstractmethod
    def open(self):
        """Open the mixer and start monitoring for volume changes."""

    @abstractmethod
    def close(self):
        """Close the mixer."""

    @property
    @abstractmethod
    def volume(self):
        """
        Get the current volume as a float.

        :return: volume, between 0.0 and 1.0
        :rtype: float
        """

    @volume.setter
    @abstractmethod
    def volume(self, value):
        """
        Set the current volume as a float.

        :param float value: the new volume, between 0.0 and 1.0
        """

    def on_volume_changed(self, value):
        """
        Subclasses should call this when the volume is changed outside of this app.

        :param float value: the new volume, between 0.0 and 1.0
        """
        smokesignal.emit(signals.CHANGE_VOLUME, value)
