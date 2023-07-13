import machine
from time import sleep
import uasyncio as asyncio

from .fonts import default as default_font

rtc = machine.RTC()


class FontDriver:

    variable_mode = True

    # Used if variable_mode = False
    char_width = 6

    chars_font_bounds = {}

    space_between_char = 1

    callback_text_write_char = None

    def __init__(self, galactic, graphics, font=default_font):
        self.galactic = galactic
        self.graphics = graphics
        self.font = font

        if self.variable_mode:
            self.load_chars_font_bounds()

    def iter_pixel(self, char):
        """Iter pixel
        Yield only lighted pixel
        """
        for y, c in enumerate(self.font[char]):
            for bit in range(8):
                if c & (1 << bit):
                    yield (bit, y)

    def load_chars_font_bounds(self):
        self.chars_font_bounds = {}
        for char in self.font:
            min_x = 1000
            max_x = 0
            for (pos_x, pos_y) in self.iter_pixel(char):
                min_x = min(min_x, pos_x)
                max_x = max(max_x, pos_x)
            self.chars_font_bounds[char] = (min_x, max_x)

    def iter_chars(self, text):
        offset = 0
        for i, char in enumerate(text):
            if self.variable_mode:
                dims = self.chars_font_bounds[char]
                offset -= dims[0]

            yield (
                char,
                offset,
                dims[1] + 1 if self.variable_mode else self.char_width,
            )

            if self.variable_mode:
                offset += dims[1] + 1 + self.space_between_char
            else:
                offset += self.char_width + self.space_between_char

    def get_chars_bounds(self, text):
        yield from self.iter_chars(text)

    def write_char(self, char, x, y=0):
        char = str(char)

        try:
            character = self.font[str(char)]
        except KeyError:
            raise Exception("Character '%s' not found in font." % char)

        for (px, py) in self.iter_pixel(char):
            self.graphics.pixel(x + px, y + py)

    def write_text(self, text, x, y):
        for i, (char, offset, _) in enumerate(self.iter_chars(text)):
            if self.callback_text_write_char:
                self.callback_text_write_char(char, i)

            self.write_char(char, x + offset, y)


class Clock(FontDriver):

    x = 0
    y = 0
    utc_offset = 0
    show_seconds = False
    font_color = None
    background_color = None

    def __init__(
            self,
            galactic,
            graphics,
            x=0,
            y=0,
            utc_offset=0,
            show_seconds=False,
            am_pm_mode=False,
            font_color=None,
            background_color=None,
        ):
        super().__init__(galactic, graphics)
        self.x = x
        self.y = y
        self.utc_offset = utc_offset
        self.show_seconds = show_seconds
        self.am_pm_mode = am_pm_mode
        
        if font_color is None:
            self.font_color = self.graphics.create_pen(255, 255, 255)

        if background_color is None:
            self.background_color = self.graphics.create_pen(0, 0, 0)

        self.format_string = '{:02}:{:02}:{:02}' if show_seconds else \
            '{:02}:{:02}'

        self.chars_bounds = [
            x for x in self.get_chars_bounds(
                self.format_string.format('0', '0', '0'),
            )
        ]

        if self.x == -1:
            # Put to the right
            _, total, width = self.chars_bounds[-1]
            self.x = self.galactic.WIDTH - total - width

    def format_time(self, hour, minute, second):
        if self.am_pm_mode:
            hour = hour % 12 if hour != 12 else hour
        else:
            hour = hour % 24
        return self.format_string.format(hour, minute, second)

    def callback_text_write_char(self, char, index):
        self.graphics.set_pen(self.font_color)

    async def test(self):
        seconds = minutes = hours = 0
        while True:
            seconds += 1
            if seconds == 60:
                minutes += 1
                seconds = 0
                if minutes == 60:
                    hours += 1
                    minutes = 0
                    if hours == 24:
                        hours = 0

            time = '{:02}:{:02}:{:02}'.format(hours, minutes, seconds)
            #time = '{:02}:{:02}'.format(minutes, seconds)
            print(time)
            #sleep(0.05)
            sleep(0.1)
            await self.animation(time)

    def iter_on_changes(self, time):
        """Get information about the changes between last_time and time"""
        for i, (last_char, char) in enumerate(zip(self.last_time, time)):
            if last_char != char:
                yield (
                    i,
                    self.chars_bounds[i][1],
                    self.chars_bounds[i][2],
                    last_char,
                    char,
                )

    def write_time(self, time):
        self.graphics.set_pen(self.font_color)
        self.write_text(time, self.x, self.y)
        self.galactic.update(self.graphics)

    last_time = None
    async def update_time(self, time):
        if self.last_time is None:
            self.write_time(time)
            self.last_time = time

        _, HEIGHT = self.graphics.get_bounds()

        for index, offset, size, _, character in self.iter_on_changes(time):
            self.graphics.set_clip(self.x + offset, 0, size, HEIGHT)
            self.graphics.set_pen(self.background_color)
            self.graphics.clear()

            self.callback_text_write_char(character, index)
            self.write_char(character, self.x + offset, self.y)

        self.galactic.update(self.graphics)

        self.last_time = time

    def get_time(self):
        _, _, _, _, hour, minute, second, _ = rtc.datetime()
        return hour, minute, second

    async def run(self):
        last_second = None
        while True:
            hour, minute, second = self.get_time()

            if second == last_second:
                asyncio.sleep(0.25)
                continue

            await self.update_time(self.format_time(
                hour + self.utc_offset,
                minute,
                second,
            ))

            last_second = second

            await asyncio.sleep(0.1)


class ClockAnimationMixin:

    async def update_time(self, time):
        if self.last_time is None:
            self.write_time(time)
            self.last_time = time

        _, HEIGHT = self.graphics.get_bounds()

        char = 0
        y = self.y
        for i in range(HEIGHT * 2 + 1):
            for index, offset, size, a, b in self.iter_on_changes(time):
                character = a if i <= HEIGHT else b

                self.graphics.set_clip(self.x + offset, 0, size, HEIGHT)
                self.graphics.set_pen(self.background_color)
                self.graphics.clear()

                self.callback_text_write_char(character, index)
                self.write_char(character, self.x + offset, y)

            self.galactic.update(self.graphics)

            y += 1
            if y >= HEIGHT:
                char += 1
                if char == 10:
                    char = 0
                y = -HEIGHT

            sleep(0.01)

        self.last_time = time