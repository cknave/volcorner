#!/usr/bin/env python

import signal
import sys

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4 import QtGui


class SegmentItem(QtGui.QGraphicsItem):
    def __init__(self, empty_filename, full_filename):
        super().__init__()
        self._empty = QtGui.QPixmap(empty_filename)
        self._full = QtGui.QPixmap(full_filename)
        self._buffer = bytearray(self.full.width() * self.full.height() * 4)  # WxH 32bpp buffer
        self.travel = self._find_total_travel(self.full, self.buffer)
        self._value = 1.0
        self._update_image()

    @property
    def empty(self):
        return self._empty

    @property
    def full(self):
        return self._full

    @property
    def buffer(self):
        return self._buffer

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            self._value = value
            self._update_image()
            self.update()  # Trigger a repaint

    def paint(self, painter, option, widget=None):
        """
        Draw the segment.

        :param QtGui.QPainter painter: the painter
        """
        if isinstance(self.image, QtGui.QPixmap):
            painter.drawPixmap(0, 0, self.image)
        else:
            painter.drawImage(0, 0, self.image)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.full.width(), self.full.height())

    def _update_image(self):
        # Special case: for 0.0, just use the empty pixmap
        if self._value == 0.0:
            self.image = self.empty
            return

        # Special case: for 1.0, draw full over top of empty, no masking needed
        if self._value == 1.0:
            self.image = QtGui.QImage(self.buffer, self.full.width(), self.full.height(),
                                      QtGui.QImage.Format_ARGB32_Premultiplied)
            painter = QtGui.QPainter(self.image)
            painter.drawPixmap(0, 0, self.empty)
            painter.drawPixmap(0, 0, self.full)
            return

        # Create a custom image for values in between.
        self.image = self._make_image(self.empty, self.full, self.buffer, self._value, self.travel)

    @classmethod
    def _make_image(cls, empty, full, buffer, value, travel):
        # Create a new image.
        image = QtGui.QImage(buffer, full.width(), full.height(), QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QtGui.QPainter(image)

        # Draw the full image to use its alpha channel.
        painter.drawPixmap(0, 0, full)

        # Draw the full image into the alpha channel, offset by the current value.
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        offset = 0 - int((1.0 - value) * travel)
        painter.drawPixmap(offset, offset, full)

        # Draw the empty image behind the partial full image.
        if empty is not None:
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_DestinationOver)
            painter.drawPixmap(0, 0, empty)
        return image

    @classmethod
    def _find_total_travel(cls, full, buffer):
        # Keep offsetting travel further until the resulting image is empty
        for travel in range(1, full.width()):
            image = cls._make_image(None, full, buffer, 0.0, travel)
            if cls._image_is_empty(image):
                return travel
        # No?  Offset the entire image then.
        return full.width()

    @classmethod
    def _image_is_empty(cls, image):
        for y in range(0, image.height()):
            for x in range(0, image.width()):
                pixel = image.pixel(x, y)
                if QtGui.qAlpha(pixel) > 0:
                    return False
        return True


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

    def animate(scale1, scale2, rotate1, rotate2, easing, duration=300, interval=16, segment_step=0.2):
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

    # Periodically change the value.
    global current_value, increment
    current_value = 0.0
    increment = 0.05

    def update_value():
        global current_value, increment
        current_value += increment
        if current_value < 0.0:
            current_value = 0.0
            increment = 0 - increment
        if current_value > 1.0:
            current_value = 1.0
            increment = 0 - increment
        set_segment_values(segments, current_value)
        QtCore.QTimer.singleShot(250, update_value)
    update_value()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
