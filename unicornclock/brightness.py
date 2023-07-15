import uasyncio as asyncio

# Todo:
# - Change the brightness smoothly

def mapval(value, in_min, in_max, out_min, out_max):
    return (
        (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    )


class Brightness:

    MODE_AUTO = 0
    MODE_MANUAL = 1

    mode = MODE_AUTO
    level = 50
    offset = 0

    def __init__(
            self,
            galactic,
            level=50,
            mode=MODE_AUTO,
            offset=20,
        ):
        self.galactic = galactic
        self.level = level
        self.mode = mode
        self.offset = offset

    def export(self):
        return {
            'mode': 'manual',
            'level': self.level,
            'current': self.galactic.get_brightness(),
        } if self.mode == self.MODE_MANUAL else {
            'mode': 'auto',
            'level': self.get_auto_level(),
            'offset': self.offset,
            'current': self.galactic.get_brightness(),
        }

    def get_corrected_level(self, level):
        return mapval(level, 0, 100, 0, 1)

    def get_auto_level(self):
        return mapval(self.galactic.light(), 0, 4095, 1, 100)

    def update(self):
        value = self.level if self.mode == self.MODE_MANUAL else \
            self.get_auto_level()

        self.galactic.set_brightness(
            self.get_corrected_level(value + self.offset)
        )

    def set_mode(self, mode, offset=0):
        """Set the brightness mode
        `mode` is MODE_AUTO or MODE_MANUAL
        """
        self.mode = mode
        self.offset = offset

    def set_level(self, level):
        """Set the brightness level
        `level` need to be integer between 0 and 100
        """
        self.level = level

    def adjust(self, value):
        """Adjust the brightness
        `level` need to be integer between 0 and 100
        """
        if self.mode == self.MODE_MANUAL:
            self.galactic.adjust_brightness(self.get_corrected_level(value))
        else:
            self.offset += value

    async def run(self):
        while True:
            self.update()
            await asyncio.sleep(1)