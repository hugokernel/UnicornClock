

class Clip:

    def __init__(self, graphics, x, y, width, height):
        self.graphics = graphics
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __enter__(self):
        self.graphics.set_clip(self.x, self.y, self.width, self.height)

    def __exit__(self, *args):
        self.graphics.remove_clip()


class Position:
    LEFT = '__left__'
    CENTER = '__center__'
    RIGHT = '__right__'


class ClockMixin:

    x = 0 # Calculated x position
    y = 0 # Calculated y position

    def set_position(self, x, y=None):
        if x == Position.LEFT:
            self.x = 0
        elif x in (Position.CENTER, Position.RIGHT):
            self.x = self.galactic.WIDTH - self.width
            if x == Position.CENTER:
                self.x = int(self.x / 2)
        else:
            self.x = x

        if y is not None:
            self.y = y
