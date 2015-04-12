#!/usr/bin/env python

import signal
import sys

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4 import QtGui

def main():
    # Use the default ctrl-c handler so we can be killed while running
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtGui.QApplication(sys.argv)

    # Load images
    bg_pixmap = QtGui.QPixmap("background.png")
    segment_pixmaps = [QtGui.QPixmap("segment{}.png".format(i)) for i in range (0,5)]

    # Place in scene
    scene = QtGui.QGraphicsScene()
    background = scene.addPixmap(bg_pixmap)
    segments = [scene.addPixmap(pixmap) for pixmap in segment_pixmaps]
    print("segment transform origin =", segments[0].transformOriginPoint().x(), segments[0].transformOriginPoint().y())

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

    animations = {}

    def animate():
        timeline = QtCore.QTimeLine(400)
        timeline.setUpdateInterval(16)
        timeline.setEasingCurve(QtCore.QEasingCurve.OutQuad)

        scale = QtGui.QGraphicsItemAnimation()
        scale.setItem(background)
        scale.setTimeLine(timeline)
        scale.setScaleAt(0.0, 0.0, 0.0)
        scale.setScaleAt(1.0, 1.0, 1.0)
        animations['scale'] = scale  # Prevent GC

        STEP = 0.2
        for i, segment in enumerate(reversed(segments)):
            rotate = QtGui.QGraphicsItemAnimation()
            rotate.setItem(segment)
            rotate.setTimeLine(timeline)
            rotate.setRotationAt(0.0, -90.0)
            rotate.setRotationAt(0.0 + STEP * i, -90.0)
            rotate.setRotationAt(1.0, 0.0)
            animations['rotate{}'.format(i)] = rotate  # Prevent GC

        timeline.start()

    view.mousePressEvent = lambda e: animate()


    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
