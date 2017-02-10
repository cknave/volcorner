"""Qt user interface."""

import asyncio
import json
import logging
import os.path
from pkg_resources import resource_filename
import struct

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtX11Extras import QX11Info
from quamash import QEventLoop
import sip
import xcffib
import xcffib.shape
import xcffib.xfixes
import xcffib.xproto
from xcffib._ffi import ffi  # Seems to be no public way to parse an event pointer

import volcorner
from volcorner.corner import Corner
from volcorner.rect import Rect
from volcorner.ui import XCBUI

_log = logging.getLogger("qtgui")

# Animation duration in ms
DURATION = 200

# X11 desktop ID for "all desktops"
ALL_DESKTOPS = -1


class QtUI(XCBUI):
    """Qt user interface."""
    def __init__(self):
        super().__init__()
        self.app = OverlayApplication()
        self.xcb_connection = self.app.xcb_connection
        self._eventFilters = {}
        self.loaded = False

    def load(self):
        self.app.load()
        self.app.on_update_volume(self.volume)
        self.app.on_update_rect(self.overlay_rect)

    def set_event_loop(self):
        loop = QEventLoop(self.app)
        asyncio.set_event_loop(loop)

    def show(self):
        self.app.show_overlay.emit()

    def hide(self):
        self.app.hide_overlay.emit()

    @property
    def corner(self):
        return super().corner

    # Can't call super().property.__set__: http://bugs.python.org/issue14965
    @corner.setter
    def corner(self, corner):
        XCBUI.corner.__set__(self, corner)
        self.app.corner = corner
        self.app.update_transform.emit(corner)

    @property
    def overlay_rect(self):
        return super().overlay_rect

    # Can't call super().property.__set__: http://bugs.python.org/issue14965
    @overlay_rect.setter
    def overlay_rect(self, overlay_rect):
        XCBUI.overlay_rect.__set__(self, overlay_rect)
        self.app.overlay_rect = overlay_rect
        self.app.update_rect.emit(overlay_rect)

    @property
    def volume(self):
        return super().volume

    # Can't call super().property.__set__: http://bugs.python.org/issue14965
    @volume.setter
    def volume(self, volume):
        XCBUI.volume.__set__(self, volume)
        self.app.update_volume.emit(volume)

    def install_event_filter(self, event_filter):
        # Wrap filter function in required class
        filter_obj = NativeEventFilter(self.xcb_connection, event_filter)
        self._eventFilters[event_filter] = filter_obj
        self.app.installNativeEventFilter(filter_obj)

    def remove_event_filter(self, event_filter):
        # Uninstall previously wrapped filter object
        try:
            filter_obj = self._eventFilters[event_filter]
        except KeyError:
            _log.warning("Tried to uninstall event filter that's not installed: %r", event_filter)
            return
        self.app.removeNativeEventFilter(filter_obj)


class OverlayApplication(QtWidgets.QApplication):
    show_overlay = QtCore.pyqtSignal()
    hide_overlay = QtCore.pyqtSignal()
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
        self.xcb_connection = self.wrap_connection()

        self.show_overlay.connect(self.on_show)
        self.hide_overlay.connect(self.on_hide)
        self.update_transform.connect(self.on_update_transform)
        self.update_volume.connect(self.on_update_volume)
        self.update_rect.connect(self.on_update_rect)

        # TODO: can Qt do 1-bit alpha channel?
        # Qt5 lost isCompositingManagerRunning() until 5.7
        if (hasattr(QX11Info, 'isCompositingManagerRunning') and
                not getattr(QX11Info, 'isCompositingManagerRunning')()):
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
        if self.segments is None:
            return
        assert 0.0 <= volume <= 1.0
        step = 1.0 / len(self.segments)
        for i, segment in enumerate(self.segments):
            relative_value = (volume - i * step) / step
            segment.value = clamp(0.0, relative_value, 1.0)

    def on_update_rect(self, rect):
        if self.window is None:
            return
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
            window_id = int(self.window.winId())
            set_window_desktop(self.xcb_connection, window_id, ALL_DESKTOPS)
            set_empty_window_shape(self.xcb_connection, self.xcb_connection.xfixes, window_id)
            self.xcb_connection.flush()

    @staticmethod
    def wrap_connection():
        """
        Wrap the current Qt xcb connection in an xcffib Connection object.

        :return: xcffib object
        """
        qt_conn = QX11Info.connection()
        conn_ptr = sip.unwrapinstance(qt_conn)
        conn = xcffib.wrap(conn_ptr)
        conn.xfixes = _load_xfixes(conn)
        return conn


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


def set_window_desktop(conn, window_id, desktop):
    """Set the virtual desktop for a window.

    :param xcffib.Connection conn: XCB connection
    :param window_id: window to change
    :param desktop: desktop to set, or ALL_DESKTOPS to show on all desktops
    """
    net_wm_desktop = _intern_atom(conn, '_NET_WM_DESKTOP')
    conn.core.ChangeProperty(xcffib.xproto.PropMode.Replace,
                             window_id,
                             net_wm_desktop,
                             xcffib.xproto.Atom.CARDINAL,
                             32,
                             1,
                             struct.pack('i', desktop),
                             is_checked=True)


def set_empty_window_shape(conn, xfixes, window_id):
    """Set an empty input shape on a window.

    This will prevent the window from receiving any input.

    :param xcffib.Connection conn: XCB connection
    :param xcffib.xfixes.xfixesExtension xfixes: XFixes extension
    :param int window_id: window to change
    """
    region_id = conn.generate_id()
    xfixes.CreateRegion(region_id, 0, [])
    xfixes.SetWindowShapeRegion(window_id, xcffib.shape.SK.Input, 0, 0, region_id,
                                is_checked=True)


def _intern_atom(conn, name):
    """Get an atom for a string.

    :param xcffib.Connection: XCB connection
    :param str name: string to look up
    :returns: atom
    :rtype: int
    """
    return conn.core.InternAtom(False, len(name), name).reply().atom


def _load_xfixes(conn):
    """Return the XFixes extension, checking for at least version 2.

    :param xcffib.Connection conn: XCB connection
    :raises ValueError: if a compatible XFixes extension is not present
    :returns: the XFixes extension
    :rtype: xcffib.xfixes.xfixesExtension
    """
    xfixes_major, xfixes_minor = (2, 0)
    try:
        xfixes = conn(xcffib.xfixes.key)
        reply = xfixes.QueryVersion(xfixes_major, xfixes_minor).reply()
    except:
        _log.error("Failed to get XFixes 2", exc_info=True)
        raise ValueError("XFixes 2 is required.")
    if reply.major_version < 2:
        _log.error("Need XFixes 2, but only %d.%d is avaliable", reply.major_version,
                   reply.minor_version)
        raise ValueError("XFixes 2 is required.")
    return xfixes


class NativeEventFilter(QtCore.QAbstractNativeEventFilter):
    def __init__(self, conn, event_filter):
        super().__init__()
        self.conn = conn
        self.event_filter = event_filter

    # Detected method signature is wrong.  Should be:
    # nativeEventFilter(self, Union[QByteArray, bytes, bytearray], sip.voidptr) -> Tuple[bool, int]
    # noinspection PyMethodOverriding
    def nativeEventFilter(self, event_type, message):
        if event_type != 'xcb_generic_event_t':
            _log.warning('Unexpected native event type %s', event_type)
            return False, 0
        generic_event = ffi.cast('xcb_generic_event_t *', message)
        event = self.conn.hoist_event(generic_event)
        result = self.event_filter(event)
        dummy_result = 0  # Used on windows apparently
        return bool(result), dummy_result
