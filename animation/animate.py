#!/usr/bin/env python

import json
import signal
import sys

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4 import QtGui


class SegmentItem(QtGui.QGraphicsItem):
    def __init__(self, config_json):
        super().__init__()
        # Convert the PIL bbox into a QRectF and QRect (both are annoyingly needed)
        json_bbox = config_json['bbox']
        self.bboxf = QtCore.QRectF(json_bbox[0],
                                   json_bbox[1],
                                   json_bbox[2] - json_bbox[0],
                                   json_bbox[3] - json_bbox[1])
        self.bbox = self.bboxf.toAlignedRect()
        # Load the images, cropping to their bounding box
        self.empty = self._cropped_image(config_json['empty'], self.bbox)
        self.full = self._cropped_image(config_json['full'], self.bbox)
        self.travel = config_json['travel']
        # Set a default value
        self._value = 1.0
        # Create the image combined image
        self._update_image()

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
        painter.drawPixmap(self.bbox.topLeft(), self.image)

    def boundingRect(self):
        return self.bboxf

    def _update_image(self):
        # Special case: for 0.0, just use the empty pixmap
        if self._value == 0.0:
            self.image = self.empty
            return

        # Combine the empty and an offset full image to make the image for a value.
        self.image = self._make_image(self.empty, self.full, self._value, self.travel)

    @classmethod
    def _make_image(cls, empty, full, value, travel):
        width = empty.width()
        height = empty.height()
        # Create a new image.
        buffer = bytearray(width * height * 4)  # QImage is 4 bytes/pixel
        image = QtGui.QImage(buffer, width, height, QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QtGui.QPainter(image)

        # Draw the full image to use its alpha channel.
        painter.drawPixmap(0, 0, full)

        # Draw the full image into the alpha channel, offset by the current value.
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        offset = 0 - int((1.0 - value) * travel)
        painter.drawPixmap(offset, offset, full)

        # Clear any remaining parts of the full image beyond the drawn rectangle.
        right_edge = full.width() + offset
        bottom_edge = full.height() + offset
        right_margin = QtCore.QRect(right_edge, 0, -offset, full.height())
        bottom_margin = QtCore.QRect(0, bottom_edge, full.width() + offset, -offset)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
        painter.fillRect(right_margin, Qt.transparent)
        painter.fillRect(bottom_margin, Qt.transparent)

        # Draw the empty image behind the partial full image.
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_DestinationOver)
        painter.drawPixmap(0, 0, empty)
        del painter  # Prevent PyQt crash
        return QtGui.QPixmap.fromImage(image)

    @classmethod
    def _cropped_image(cls, filename, bbox):
        image = QtGui.QImage(filename)
        cropped = image.copy(bbox)
        return QtGui.QPixmap.fromImage(cropped)


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
    with open('segments.json') as config_file:
        config_json = json.load(config_file)
    segments = [SegmentItem(segment_config) for segment_config in config_json['segments']]

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
