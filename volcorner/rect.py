"""Rectangle structure."""

from collections import namedtuple

__all__ = [
    'Point',
    'Size',
    'Rect',
]
Point = namedtuple('Point', 'x y')
Size = namedtuple('Size', 'width height')


class Rect(namedtuple('Rect', 'origin size')):
    """A rectangle."""
    __slots__ = ()

    @classmethod
    def make(cls, x, y, width, height):
        origin = Point(x, y)
        size = Size(width, height)
        return cls(origin, size)

    @property
    def x1(self):
        return self.origin.x

    @property
    def y1(self):
        return self.origin.y

    @property
    def width(self):
        return self.size.width

    @property
    def height(self):
        return self.size.height

    @property
    def x2(self):
        return self.origin.x + self.size.width - 1

    @property
    def y2(self):
        return self.origin.y + self.size.height - 1

    def contains(self, point):
        """
        Test if this Rect contains a point.

        :param Point point: The point to test
        :return: True if this Rect contains the point
        """
        px, py = point
        x1, y1 = self.origin
        x2, y2 = self.x2, self.y2
        return (x1 <= px <= x2) and (y1 <= py <= y2)
