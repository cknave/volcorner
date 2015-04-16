#!/usr/bin/env python

import signal
import sys

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4 import QtGui


class SegmentItem(QtGui.QGraphicsItem):
    def __init__(self, filename):
        super().__init__()
        self.pixmap = QtGui.QPixmap(filename)
        self.value = 1.0

    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self.pixmap)
        # TODO: fill with value (0-1)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.pixmap.width(), self.pixmap.height())


def main():
    # Use the default ctrl-c handler so we can be killed while running
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtGui.QApplication(sys.argv)

    # Load images
    bg_pixmap = QtGui.QPixmap("background.png")
    segments = [SegmentItem("segment{}.png".format(i)) for i in range(0, 5)]

    # Place in scene
    scene = QtGui.QGraphicsScene()
    background = scene.addPixmap(bg_pixmap)
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

        for i, segment in enumerate(reversed(segments)):
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
