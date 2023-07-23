import uasyncio as asyncio

from .common import Position


class Calendar:
    """Calendar widget

    Draw a calendar frame with the day
    """

    width = 12
    height = 11
    banner_height = 3

    def __init__(
            self,
            galactic,
            graphics,
            x=0,
            y=0,
            background_color=None,
            banner_color=None,
            day_color=None,
            rtc=None,
        ):
        self.galactic = galactic
        self.graphics = graphics
        self.background_color = background_color
        self.banner_color = banner_color
        self.day_color = day_color

        if self.background_color is None:
            self.background_color = self.graphics.create_pen(255, 255, 255)

        if self.banner_color is None:
            self.banner_color = self.graphics.create_pen(255, 0, 0)

        if self.day_color is None:
            self.day_color = self.graphics.create_pen(0, 0, 255)

        self.set_position(x, y)

        if rtc is None:
            import machine
            self.rtc = machine.RTC()

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

    def get_day(self):
        _, _, day, _, _, _, _, _ = self.rtc.datetime()
        return day

    def draw_frame(self):
        self.graphics.set_pen(self.banner_color)
        self.graphics.rectangle(self.x, self.y, self.width,
                                self.banner_height)

        self.graphics.set_pen(self.background_color)
        self.graphics.rectangle(self.x, self.y + self.banner_height,
                                self.width,
                                self.height - self.banner_height)

    def draw_day(self, day):
        width = self.graphics.measure_text(day, 1)

        # We are trying to center the day
        offset = 0
        if width < 6:
            offset = 3
        elif width < 7:
            offset = 2
        elif width in (8, 9):
            offset = 1

        self.graphics.set_pen(self.day_color)
        self.graphics.text(day, self.x + 1 + offset, self.y + 3, -1, 1)

    def draw_all(self):
        self.draw_frame()

        self.draw_day(str(self.get_day()))

    async def run(self):
        while True:
            self.draw_all()

            self.galactic.update(self.graphics)

            await asyncio.sleep(30)
