"""Corner tests."""

from nose.tools import raises

from volcorner.rect import Rect, Size
from volcorner.corner import Corner


TEST_SCREEN = Size(100, 100)
TEST_SIZE = Size(1, 1)


def test_top_left():
    """Test calculating the top left corner."""
    corner = Corner.TOP_LEFT.rect(TEST_SCREEN, TEST_SIZE)
    assert corner == Rect.make(0, 0, 1, 1)


def test_top_right():
    """Test calculating the top left corner."""
    corner = Corner.TOP_RIGHT.rect(TEST_SCREEN, TEST_SIZE)
    assert corner == Rect.make(99, 0, 1, 1)


def test_bottom_left():
    """Test calculating the top left corner."""
    corner = Corner.BOTTOM_LEFT.rect(TEST_SCREEN, TEST_SIZE)
    assert corner == Rect.make(0, 99, 1, 1)


def test_bottom_right():
    """Test calculating the top left corner."""
    corner = Corner.BOTTOM_RIGHT.rect(TEST_SCREEN, TEST_SIZE)
    assert corner == Rect.make(99, 99, 1, 1)


def test_get_from_id():
    """Test getting a corner from its ID."""
    assert Corner.from_id('top-left') is Corner.TOP_LEFT
    assert Corner.from_id('top-right') is Corner.TOP_RIGHT
    assert Corner.from_id('bottom-left') is Corner.BOTTOM_LEFT
    assert Corner.from_id('bottom-right') is Corner.BOTTOM_RIGHT


@raises(ValueError)
def test_get_from_invalid_id():
    """Test getting an invalid corner."""
    Corner.from_id('aoeu')
