import machine
from time import sleep
import uasyncio as asyncio

from .fontdriver import FontDriver

rtc = machine.RTC()


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