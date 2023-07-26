import uasyncio as asyncio

from .common import Clip, Position
from .fonts import default as default_font
from .fontdriver import FontDriver


class Clock(FontDriver):

    x = 0
    y = 0
    show_seconds = False
    font_color = None
    background_color = None

    callback_hour_change = None

    def __init__(
            self,
            galactic,
            graphics,
            x=0,
            y=0,
            show_seconds=False,
            am_pm_mode=False,
            font_color=None,
            background_color=None,
            font=default_font,
            rtc=None,
            callback_hour_change=None,
        ):
        super().__init__(galactic, graphics, font)
        self.show_seconds = show_seconds
        self.am_pm_mode = am_pm_mode
        self.font_color = font_color
        self.background_color = background_color
        self.callback_hour_change = callback_hour_change

        if self.font_color is None:
            self.font_color = self.graphics.create_pen(255, 255, 255)

        if self.background_color is None:
            self.background_color = self.graphics.create_pen(0, 0, 0)

        if rtc is None:
            import machine
            self.rtc = machine.RTC()

        self.format_string = '{:02}:{:02}:{:02}' if show_seconds else \
            '{:02}:{:02}'

        self.chars_bounds = [
            x for x in self.get_chars_bounds(
                self.format_string.format('0', '0', '0'),
            )
        ]

        self.screen_width, self.screen_height = self.graphics.get_bounds()

        self.set_position(x, y)

    def set_position(self, x, y=None):
        if x == Position.LEFT:
            self.x = 0
        elif x in (Position.CENTER, Position.RIGHT):
            _, total, width = self.chars_bounds[-1]
            self.x = self.galactic.WIDTH - total - width
            if x == Position.CENTER:
                self.x = int(self.x / 2)
        else:
            self.x = x

        if y is not None:
            self.y = y

    def format_time(self, hour, minute, second):
        if self.am_pm_mode:
            hour = hour % 12 if hour != 12 else hour
        else:
            hour = hour % 24
        return self.format_string.format(hour, minute, second)

    def callback_write_char(self, char, index):
        self.graphics.set_pen(self.font_color)

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

        for index, offset, size, _, character in self.iter_on_changes(time):
            with Clip(self.graphics, self.x + offset, 0, size,
                      self.screen_height):
                self.graphics.set_pen(self.background_color)
                self.graphics.clear()

                self.callback_write_char(character, index)
                self.write_char(character, self.x + offset, self.y)

        self.galactic.update(self.graphics)

        self.last_time = time

    def full_update(self):
        self.last_time = None

    def get_time(self):
        _, _, _, _, hour, minute, second, _ = self.rtc.datetime()
        return hour, minute, second

    async def run(self):
        last_second = None
        last_hour = None
        while True:
            hour, minute, second = self.get_time()

            if second == last_second:
                asyncio.sleep(0.25)
                continue

            if hour != last_hour and self.callback_hour_change:
                self.callback_hour_change(hour)

            await self.update_time(self.format_time(
                hour,
                minute,
                second,
            ))

            last_second = second
            last_hour = hour

            await asyncio.sleep(0.1)

    async def test(self):
        """Test method

        Used to do some test when debugging animation or what you want...
        Call this method instead run.
        """
        second = minute = hour = 0
        while True:
            second += 1
            if second == 60:
                minute += 1
                second = 0
                if minute == 60:
                    hour += 1
                    minute = 0

            time = '{:02}:{:02}:{:02}'.format(hour, minute, second)
            print(time)
            asyncio.sleep(0.01)
            await self.update_time(self.format_time(
                hour,
                minute,
                second,
            ))