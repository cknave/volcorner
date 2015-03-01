"""Abstract base audio mixer."""

from abc import ABCMeta, abstractmethod
from fastvol import signals
import smokesignal


class Mixer(metaclass=ABCMeta):
    @abstractmethod
    def get_volume(self):
        """
        Get the current volume as a float.

        :return: volume, between 0.0 and 1.0
        :rtype: float
        """

    @abstractmethod
    def set_volume(self, value):
        """
        Set the current volume as a float.

        :param float value: the new volume, between 0.0 and 1.0
        """

    def on_volume_changed(self, value):
        """
        Subclasses should call this when the volume is changed outside of this app.

        :param float value: the new volume, between 0.0 and 1.0
        """
        smokesignal.emit(signals.VOLUME_CHANGED, value)