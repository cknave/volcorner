#!/usr/bin/env python

import signal
import sys

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4 import QtGui


class SegmentItem(QtGui.QGraphicsItem):
    def __init__(self, empty_filename, full_filename):
        super().__init__()
        self.empty = QtGui.QPixmap(empty_filename)
        self.full = QtGui.QPixmap(full_filename)
        self.mask = self.full.mask()
        self.travel = self._find_total_travel(self.full, self.mask)
        self._value = 1.0

    @property
    def value(self):
        return self._value

    @value.setter
    def set_value(self, value):
        if value != self._value:
            self._value = value
            self.update()  # Trigger a repaint

    def paint(self, painter, option, widget):
        """
        Draw the segment.

        :param QtGui.QPainter painter: the painter
        """
        # painter.drawPixmap(0, 0, self.full)
        # TODO: fill with value (0-1)
        # Test mask
        painter.drawPixmap(0, 0, self.empty)
        painter.setClipRegion(QtGui.QRegion(self.mask))
        painter.translate(-5, -5)
        painter.drawPixmap(0, 0, self.full)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.full.width(), self.full.height())

    @staticmethod
    def _find_total_travel(full, mask):
        return 10  # TODO: keep offsetting full until no pixels are drawn


def set_segment_values(segments, value):
    assert 0.0 <= value <= 1.0
    step = 1.0 / len(segments)
    for i, segment in enumerate(segments):
        relative_value = (value - i * step) / step
        segment.value = clamp(0.0, relative_value, 1.0)


def clamp(minimum, value, maximum):
    return max(minimum, min(maximum, value))


def main():
    # Use the default ctrl-c handler so we can be killed while running
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtGui.QApplication(sys.argv)

    # Load images
    bg_pixmap = QtGui.QPixmap("background.png")
    dot_pixmap = QtGui.QPixmap("segment_full0.png")
    image_pairs = [tuple(s.format(i) for s in ("segment_empty{}.png", "segment_full{}.png"))
                   for i in range(1, 5)]
    segments = [SegmentItem(*pair) for pair in image_pairs]

    # Place in scene
    scene = QtGui.QGraphicsScene()
    background = scene.addPixmap(bg_pixmap)
    dot = scene.addPixmap(dot_pixmap)
    for segment in segments:
        scene.addItem(segment)

    # Create and show scene window
    view = QtGui.QGraphicsView(scene)
    view.setStyleSheet("background-color: transparent;")
    view.setFixedSize(200, 200)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    view.setWindowTitle("Animation")
    view.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    view.setAttribute(Qt.WA_TranslucentBackground)
    view.setFrameStyle(QtGui.QFrame.NoFrame)

    # This doesn't seem to have any effect
    view.setRenderHint(QtGui.QPainter.Antialiasing)
    view.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)

    view.show()

    # Use negative scale (and sometimes transform) to flip
    #
    # top-right
    # view.scale(-1.0, 1.0)
    #
    # bottom-left
    # view.scale(1.0, -1.0)
    # view.translate(0, -200)
    #
    # bottom-right
    # view.scale(-1.0, -1.0)
    # view.translate(0, -200)

    animations = {}

    def animate(scale1, scale2, rotate1, rotate2, easing, duration=300, interval=16,
                segment_step=0.2):
        timeline = QtCore.QTimeLine(duration)
        timeline.setUpdateInterval(interval)
        timeline.setEasingCurve(easing)

        scale = QtGui.QGraphicsItemAnimation()
        scale.setItem(background)
        scale.setTimeLine(timeline)
        scale.setScaleAt(0.0, scale1, scale1)
        scale.setScaleAt(1.0, scale2, scale2)
        animations['scale'] = scale  # Prevent GC

        for i, segment in enumerate(reversed([dot] + segments)):
            rotate = QtGui.QGraphicsItemAnimation()
            rotate.setItem(segment)
            rotate.setTimeLine(timeline)
            rotate.setRotationAt(0.0, rotate1)
            rotate.setRotationAt(0.0 + segment_step * i, rotate1)
            rotate.setRotationAt(1.0, rotate2)
            animations['rotate{}'.format(i)] = rotate  # Prevent GC

        timeline.start()

    view.enterEvent = lambda e: animate(scale1=0.0, scale2=1.0, rotate1=-90.0, rotate2=0.0,
                                        easing=QtCore.QEasingCurve.OutQuad)
    view.leaveEvent = lambda e: animate(scale1=1.0, scale2=0.0, rotate1=0.0, rotate2=90.0,
                                        easing=QtCore.QEasingCurve.InQuad)

    # TODO: use timeline finished signal to queue up next animation

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
