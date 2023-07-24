

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
