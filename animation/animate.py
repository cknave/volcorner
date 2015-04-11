#!/usr/bin/env python

import sys

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

def main():
    app = QtGui.QApplication(sys.argv)

    # Load images
    bg_pixmap = QtGui.QPixmap("background.png")
    segments = [QtGui.QPixmap("segment{}.png".format(i)) for i in range (0,5)]

    # Place in scene
    scene = QtGui.QGraphicsScene()
    scene.addPixmap(bg_pixmap)
    for segment in segments:
        scene.addPixmap(segment)

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

    # Quit on key press
    view.keyPressEvent = lambda event: view.close()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
