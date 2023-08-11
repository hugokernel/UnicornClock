from time import sleep

from .common import Clip
from .utils import from_hsv


class CharacterSlideEffect:
    """Character slide effect"""

    # True: Down, False: Up
    direction = 1

    async def update_time(self, time):
        if self.last_time is None:
            self.write_time(time)
            self.last_time = time

        _, HEIGHT = self.graphics.get_bounds()

        y = self.y
        if not self.direction:
            y += HEIGHT + 1

        for i in range(
            (HEIGHT * 2 if self.direction else HEIGHT + 1) + 1
        ):
            for index, offset, size, a, b in self.iter_on_changes(time):
                character = a if i <= HEIGHT else b

                with Clip(self.graphics, self.x + offset, 0, size, HEIGHT):
                    self.graphics.set_pen(self.background_color)
                    self.graphics.clear()

                    self.callback_write_char(character, index)
                    self.write_char(character, self.x + offset, y)

            self.galactic.update(self.graphics)

            if self.direction:
                y += 1
                if y >= HEIGHT:
                    y = -HEIGHT
            else:
                y -= 1

            sleep(0.01)

        self.last_time = time


class CharacterSlideDownEffect(CharacterSlideEffect):
    direction = True


class CharacterSlideUpEffect(CharacterSlideEffect):
    direction = False


class RainbowMixin:

    hue_offset = 0
    hue_map = []

    def callback_after_init(self):
        info = self.chars_bounds[-1]
        self.width = info[1] + info[2]
        self.hue_map = [
            from_hsv(x / self.width, 1.0, 1.0) for x in range(self.width)
        ]

        self.separator_color = self.graphics.create_pen(255, 255, 255)

    def set_pen(self, char, i):
        color = self.separator_color

        if char != ':':
            colour = self.hue_map[
                int((i + (self.hue_offset * self.width)) % self.width)
            ]
            color = self.graphics.create_pen(
                int(colour[0]), int(colour[1]), int(colour[2])
            )

        self.graphics.set_pen(color)


class RainbowCharEffect(RainbowMixin):
    """Rainbow Char Effect

    Each character color come from a rainbow.
    """

    def callback_write_char(self, char, index):
        self.set_pen(char, index)


class RainbowPixelEffect(RainbowMixin):
    """Rainbow Pixel Effect

    Each pixel column color of character come from a rainbow.
    """

    def callback_set_pixel(self, char, x, y):
        self.set_pen(char, x)


class RainbowMoveEffect(RainbowMixin):
    """Rainbow move effect

    Colorize the characters as a rainbow and move it.
    """

    loop_sleep = 0.01

    def callback_set_pixel(self, char, x, y):
        self.set_pen(char, x)

    async def update_time(self, time):
        for character, offset, size in self.get_chars_bounds(time):
            with Clip(self.graphics, self.x + offset, self.y, size,
                      self.screen_height):
                self.graphics.set_pen(self.background_color)
                self.graphics.clear()

                self.write_char(character, self.x + offset, self.y)

        self.galactic.update(self.graphics)

    async def callback_time_updated(self, hour, minute, second):
        self.hue_offset += 0.01

    async def need_update(self, hour, minute, second):
        return True
