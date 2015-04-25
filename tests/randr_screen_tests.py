"""
X11 RandRScreen tests.

NOTE: As of xorg-server 1.17.1, RANDR is still not supported in Xvfb.  A patch is required:
https://bugzilla.novell.com/show_bug.cgi?id=823410

"""

# import subprocess
#
# from volcorner.rect import Size
# from volcorner.x11.randrscreen import RandRScreen
# from .util import SignalReceiver, with_xvfb
#
#
# @with_xvfb
# def test_size_update():
#     screen = RandRScreen()
#     screen.open()
#     try:
#         # Initial size from XvfbTest
#         assert screen.size == Size(800, 600)
#
#         # TODO: haven't been able to change the resolution.  Maybe a limitation of the patched Xvfb.
#     finally:
#         screen.close()
