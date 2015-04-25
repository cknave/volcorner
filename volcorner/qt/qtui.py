"""Qt user interface."""

import json
import logging
import os.path
from pkg_resources import resource_filename

from PyQt4 import QtCore
from PyQt4.QtCore import Qt
from PyQt4 import QtGui

import volcorner
from volcorner.corner import Corner
from volcorner.ui import UI

_log = logging.getLogger("qtgui")


class QtUI(UI):
    """Qt user interface."""
    def __init__(self):
        super().__init__()
        self.app = OverlayApplication()

    def load(self):
        self.app.load()

    def run_main_loop(self):
        self.app.exec_()

    def show(self):
        self.app.show_overlay.emit()

    def hide(self):
        self.app.hide_overlay.emit()

    def stop(self):
        self.app.stop.emit()

    @property
    def corner(self):
        return super().corner

    # Can't call super().property.__set__: http://bugs.python.org/issue14965
    @corner.setter
    def corner(self, corner):
        UI.corner.__set__(self, corner)
        self.app.corner = corner
        self.app.update_transform.emit(corner)

    @property
    def overlay_rect(self):
        return super().overlay_rect

    # Can't call super().property.__set__: http://bugs.python.org/issue14965
    @overlay_rect.setter
    def overlay_rect(self, overlay_rect):
        UI.overlay_rect.__set__(self, overlay_rect)
        self.app.overlay_rect = overlay_rect

    @property
    def volume(self):
        return super().volume

    # Can't call super().property.__set__: http://bugs.python.org/issue14965
    @volume.setter
    def volume(self, volume):
        UI.volume.__set__(self, volume)
        self.app.update_volume.emit(volume)


class OverlayApplication(QtGui.QApplication):
    show_overlay = QtCore.pyqtSignal()
    hide_overlay = QtCore.pyqtSignal()
    stop = QtCore.pyqtSignal()
    update_transform = QtCore.pyqtSignal(Corner)
    update_volume = QtCore.pyqtSignal(float)

    def __init__(self, args=[]):
        super().__init__(args)
        self.background = None
        self.dot = None
        self.segments = None
        self.show_animation = None
        self.hide_animation = None
        self.overlay_rect = None
        self.corner = None
        self.window = None

        # Use a queued connection since these can be called from another thread
        self.show_overlay.connect(self.on_show, Qt.QueuedConnection)
        self.hide_overlay.connect(self.on_hide, Qt.QueuedConnection)
        self.stop.connect(self.on_stop, Qt.QueuedConnection)
        self.update_transform.connect(self.on_update_transform, Qt.QueuedConnection)
        self.update_volume.connect(self.on_update_volume, Qt.QueuedConnection)

        # TODO: can Qt do 1-bit alpha channel?
        if not QtGui.QX11Info.isCompositingManagerRunning():
            _log.warn("Compositing window manager NOT detected!  Translucency will be broken.")

    def load(self):
        assert self.overlay_rect is not None
        assert self.corner is not None

        # Load images
        bg_pixmap = QtGui.QPixmap(path_to('background.png'))
        dot_pixmap = QtGui.QPixmap(path_to('segment_full0.png'))
        with open(path_to('segments.json')) as config_file:
            config_json = json.load(config_file)
        self.segments = [SegmentItem(config) for config in config_json['segments']]

        # Place in scene
        scene = QtGui.QGraphicsScene()
        self.background = scene.addPixmap(bg_pixmap)
        self.dot = scene.addPixmap(dot_pixmap)
        for segment in self.segments:
            scene.addItem(segment)

        # Create a window for the scene
        self.window = self._create_window(scene)

    def on_show(self):
        # TODO: handle if already hiding
        self.window.show()
        self.show_animation = self._animate(scale_in=0.0, scale_out=1.0,
                                            rotation_in=-90.0, rotation_out=0.0,
                                            easing=QtCore.QEasingCurve.OutQuad)
        # TODO: clear out show animation when done

    def on_hide(self):
        # TODO: handle if already showing
        self.hide_animation = self._animate(scale_in=1.0, scale_out=0.0,
                                            rotation_in=0.0, rotation_out=90.0,
                                            easing=QtCore.QEasingCurve.InQuad)
        # TODO: clear out hide animation when done
        # TODO: hide window when done

    def on_stop(self):
        self.quit()

    def on_update_transform(self, corner):
        if (self.window is not None) and (self.overlay_rect is not None):
            if corner == Corner.TOP_LEFT:
                self.window.scale(1.0, 1.0)
                self.window.translate(0, 0)
            elif corner == Corner.TOP_RIGHT:
                self.window.scale(-1.0, 1.0)
                self.window.translate(0, 0)
            elif corner == Corner.BOTTOM_LEFT:
                self.window.scale(1.0, -1.0)
                self.window.translate(0, 0 - self.overlay_rect.height)
            elif corner == Corner.BOTTOM_RIGHT:
                self.window.scale(-1.0, -1.0)
                self.window.translate(0, 0 - self.overlay_rect.height)

    def on_update_volume(self, volume):
        assert 0.0 <= volume <= 1.0
        step = 1.0 / len(self.segments)
        for i, segment in enumerate(self.segments):
            relative_value = (volume - i * step) / step
            segment.value = clamp(0.0, relative_value, 1.0)

    def _create_window(self, scene):
        window = QtGui.QGraphicsView(scene)
        window.setStyleSheet("background-color: transparent;")
        window.setFixedSize(self.overlay_rect.width, self.overlay_rect.height)
        window.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        window.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        window.setWindowTitle("volcorner")
        window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        window.setAttribute(Qt.WA_TranslucentBackground)
        window.setFrameStyle(QtGui.QFrame.NoFrame)
        window.move(self.overlay_rect.x1, self.overlay_rect.y1)
        self.on_update_transform(self.corner)
        return window

    def _animate(self, scale_in, scale_out, rotation_in, rotation_out, easing, duration=300,
                 interval=16, segment_step=0.2):
        animations = []

        timeline = QtCore.QTimeLine(duration)
        timeline.setUpdateInterval(interval)
        timeline.setEasingCurve(easing)

        scale = QtGui.QGraphicsItemAnimation()
        scale.setItem(self.background)
        scale.setTimeLine(timeline)
        scale.setScaleAt(0.0, scale_in, scale_in)
        scale.setScaleAt(1.0, scale_out, scale_out)
        animations.append(scale)

        for i, segment in enumerate(reversed([self.dot] + self.segments)):
            rotate = QtGui.QGraphicsItemAnimation()
            rotate.setItem(segment)
            rotate.setTimeLine(timeline)
            rotate.setRotationAt(0.0, rotation_in)
            rotate.setRotationAt(0.0 + segment_step * i, rotation_in)
            rotate.setRotationAt(1.0, rotation_out)
            animations.append(rotate)

        timeline.start()
        return animations


class SegmentItem(QtGui.QGraphicsItem):
    """Graphics item for a segment of the volume display."""
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
        image = QtGui.QImage(path_to(filename))
        cropped = image.copy(bbox)
        return QtGui.QPixmap.fromImage(cropped)


def path_to(filename):
    """Return the path to an image resource."""
    return resource_filename(volcorner.__name__, os.path.join('images', filename))


def clamp(minimum, value, maximum):
    return max(minimum, min(maximum, value))
