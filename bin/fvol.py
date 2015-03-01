#!/usr/bin/env python3
"""Fastvol volume changer."""

from fastvol.tracking import Rect
from fastvol.tracking.x11.xinput2 import XInput2MouseTracker

def main():
    """Main function."""
    tracker = XInput2MouseTracker()
    tracker.region = Rect.make(0, 0, 100, 100)
    tracker.start()

    try:
        import time
        time.sleep(999999999999)
    finally:
        tracker.stop()

if __name__ == '__main__':
    main()
