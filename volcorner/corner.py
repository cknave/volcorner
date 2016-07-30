"""Screen corners."""

from enum import Enum

from volcorner.rect import Rect


class Corner(Enum):
    """A corner of the screen."""
    TOP_LEFT     = ('top-left',     'x1',  1, 'y1',  1)
    TOP_RIGHT    = ('top-right',    'x2', -1, 'y1',  1)
    BOTTOM_LEFT  = ('bottom-left',  'x1',  1, 'y2', -1)
    BOTTOM_RIGHT = ('bottom-right', 'x2', -1, 'y2', -1)

    def __init__(self, ident, x_root, x_direction, y_root, y_direction):
        self.id = ident
        self.x_root = x_root
        self.x_direction = x_direction
        self.y_root = y_root
        self.y_direction = y_direction

    def rect(self, screen_size, corner_size):
        """
        Calculate a Rect for this Corner.

        :param Size screen_size: the screen size
        :param Size corner_size: the size of the Rect to return
        :return: the rect for this Corner
        """
        # Find the corners by starting at the root, and adding size*direction.
        # Use the screen size + 1 to offset subtracting 1 when using the bottom/right of the screen.
        screen = Rect.make(0, 0, screen_size.width + 1, screen_size.height + 1)
        x1 = getattr(screen, self.x_root)
        x2 = x1 + corner_size.width * self.x_direction
        y1 = getattr(screen, self.y_root)
        y2 = y1 + corner_size.height * self.y_direction
        # The origin should be the smaller of the coordinates.
        x_origin = min(x1, x2)
        y_origin = min(y1, y2)
        return Rect.make(x_origin, y_origin, corner_size.width, corner_size.height)

    @classmethod
    def from_id(cls, ident):
        match = [c for c in cls if c.id == ident]
        if match:
            return match[0]
        else:
            raise ValueError("Unknown Corner id {}".format(ident))
