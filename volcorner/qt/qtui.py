"""Qt user interface."""

from collections import namedtuple
import json
import logging
import os.path
from pkg_resources import resource_filename

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtX11Extras import QX11Info

import volcorner
from volcorner.corner import Corner
from volcorner.rect import Rect
from volcorner.ui import UI
from volcorner.x11 import xlib

_log = logging.getLogger("qtgui")

# Animation duration in ms
DURATION = 200


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
        self.app.update_rect.emit(overlay_rect)

    @property
    def volume(self):
        return super().volume

    # Can't call super().property.__set__: http://bugs.python.org/issue14965
    @volume.setter
    def volume(self, volume):
        UI.volume.__set__(self, volume)
        self.app.update_volume.emit(volume)


class OverlayApplication(QtWidgets.QApplication):
    show_overlay = QtCore.pyqtSignal()
    hide_overlay = QtCore.pyqtSignal()
    stop = QtCore.pyqtSignal()
    update_transform = QtCore.pyqtSignal(Corner)
    update_volume = QtCore.pyqtSignal(float)
    update_rect = QtCore.pyqtSignal(Rect)

    def __init__(self, args=None):
        super().__init__(args or [])
        self.background = None
        self.background_rotation = None
        self.background_scale = None
        self.dot = None
        self.dot_rotation = None
        self.segments = None
        self.current_animation = None
        self.next_animation = None
        self.overlay_rect = None
        self.corner = None
        self.window = None
        self._has_set_advanced_window_state = False

        # Use a queued connection since these can be called from another thread
        self.show_overlay.connect(self.on_show, Qt.QueuedConnection)
        self.hide_overlay.connect(self.on_hide, Qt.QueuedConnection)
        self.stop.connect(self.on_stop, Qt.QueuedConnection)
        self.update_transform.connect(self.on_update_transform, Qt.QueuedConnection)
        self.update_volume.connect(self.on_update_volume, Qt.QueuedConnection)
        self.update_rect.connect(self.on_update_rect, Qt.QueuedConnection)

        # TODO: can Qt do 1-bit alpha channel?
        # Qt5 lost isCompositingManagerRunning() until 5.7
        if (hasattr(QX11Info, 'isCompositingManagerRunning') and
                not QX11Info.isCompositingManagerRunning()):
            _log.warning("Compositing window manager NOT detected!  Translucency will be broken.")

    def load(self):
        assert self.overlay_rect is not None
        assert self.corner is not None

        # Load images
        bg_pixmap = QtGui.QPixmap(path_to('background.png'))
        dot_pixmap = QtGui.QPixmap(path_to('segment_full0.png'))
        with open(path_to('segments.json')) as config_file:
            config_json = json.load(config_file)
        self.segments = [SegmentObject(config) for config in config_json['segments']]

        # Place in scene
        scene = QtWidgets.QGraphicsScene()
        self.background = scene.addPixmap(bg_pixmap)
        self.background_scale = QtWidgets.QGraphicsScale()
        self.background_rotation = QtWidgets.QGraphicsRotation()
        self.background.setTransformations([self.background_scale, self.background_rotation])
        self.dot = scene.addPixmap(dot_pixmap)
        self.dot_rotation = QtWidgets.QGraphicsRotation()
        self.dot.setTransformations([self.dot_rotation])
        for segment in self.segments:
            scene.addItem(segment)

        # Create a window for the scene
        self.window = self._create_window(scene)

    def queue_animation(self, anim_func):
        if self.current_animation is None:
            _log.debug('Starting animation {}'.format(anim_func.__name__))
            self.current_animation = anim_func()
            self.current_animation.finished.connect(self.on_animation_finished)
        else:
            _log.debug('Queueing animation {}'.format(anim_func.__name__))
            self.next_animation = anim_func

    def on_animation_finished(self):
        _log.debug('Animation finished')
        self.current_animation = None
        if self.next_animation:
            self.queue_animation(self.next_animation)
            self.next_animation = None

    def on_show(self):
        self.queue_animation(self._animate_show)

    def on_hide(self):
        self.queue_animation(self._animate_hide)

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

    def on_update_rect(self, rect):
        if self.window is not None:
            self.window.move(rect.x1, rect.y1)
            self.window.setFixedSize(rect.width, rect.height)

    def _create_window(self, scene):
        window = QtWidgets.QGraphicsView(scene)
        window.setStyleSheet("background-color: transparent;")
        window.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        window.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        window.setWindowTitle("volcorner")
        window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        window.setAttribute(Qt.WA_TranslucentBackground)
        window.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.on_update_rect(self.overlay_rect)
        self.on_update_transform(self.corner)
        return window

    def _animate(self, scale_in, scale_out, rotation_in, rotation_out, easing, completion=None,
                 duration=DURATION, segment_step=0.2):
        animations = []

        for prop in (b'xScale', b'yScale'):
            scale = QtCore.QPropertyAnimation(self.background_scale, prop)
            scale.setStartValue(scale_in)
            scale.setEndValue(scale_out)
            animations.append(scale)

        for i, segment in enumerate(reversed([self.dot_rotation] + self.segments)):
            # QGraphicsRotation has 'angle' instead of 'rotation'
            prop = b'rotation' if hasattr(segment, 'rotation') else b'angle'
            rotate = QtCore.QPropertyAnimation(segment, prop)
            rotate.setTargetObject(segment)
            rotate.setStartValue(rotation_in)
            rotate.setKeyValueAt(segment_step * i, rotation_in)
            rotate.setEndValue(rotation_out)
            animations.append(rotate)

        group = QtCore.QParallelAnimationGroup()
        for animation in animations:
            animation.setDuration(duration)
            animation.setEasingCurve(easing)
            group.addAnimation(animation)

        if completion:
            group.finished.connect(completion)

        group.start()
        return group

    def _animate_show(self):
        self.window.show()
        self._set_advanced_window_state()
        return self._animate(scale_in=0.0, scale_out=1.0, rotation_in=-90.0, rotation_out=0.0,
                             easing=QtCore.QEasingCurve.OutQuad)

    def _animate_hide(self):
        return self._animate(scale_in=1.0, scale_out=0.0, rotation_in=0.0, rotation_out=90.0,
                             easing=QtCore.QEasingCurve.InQuad,
                             completion=lambda: self.window.hide())

    def _set_advanced_window_state(self):
        # Only need to set this state once.
        if not self._has_set_advanced_window_state:
            self._has_set_advanced_window_state = True

            display = QX11Info.display()
            window_id = self.window.winId()

            xlib.move_to_desktop(display, window_id, xlib.ALL_DESKTOPS)
            xlib.set_empty_window_shape(display, window_id)


class SegmentObject(QtWidgets.QGraphicsObject):
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
