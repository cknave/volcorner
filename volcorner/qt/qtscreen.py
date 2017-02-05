"""Qt screen monitor."""

import logging

from PyQt5 import QtCore

from volcorner.screen import Screen
from volcorner.rect import Size

__all__ = ['QtScreen']
_log = logging.getLogger("qtscreen")


class QtScreen(Screen):
    def __init__(self, ui):
        """Initialize a new QtScreen.

        :param volcorner.qt.qtui.QtUI ui: UI to attach to
        """
        self._desktop = ui.app.desktop()  # QtC
        self._size = None

    def open(self):
        # Select screen change events.
        self._desktop.workAreaResized.connect(self._on_resized)

        # Update the current size.
        self._update_size()
        _log.debug("Initial screen size: %r", self._size)

    def close(self):
        self._size = None

    @property
    def size(self):
        return self._size

    def _update_size(self):
        """Update the size field with the current value from the UI."""
        self._size = get_qrect_size(self._desktop.screenGeometry())

    def _on_resized(self, screen):
        """Handle a resized event."""
        # TODO: geometry doesn't update! WTF!
        self._update_size()
        self.on_resolution_changed(self._size)


def get_qrect_size(qrect):
    """Extract the Size from a QRect.

    :param PyQt5.QtCore.QRect.QRect qrect: QRect to convert
    :return: the size
    :rtype: Size
    """
    return Size(qrect.width(), qrect.height())
