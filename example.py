import machine
import network
import ntptime
import uasyncio as asyncio
from galactic import GalacticUnicorn
from picographics import DISPLAY_GALACTIC_UNICORN, PicoGraphics
from time import sleep

from unicornclock import Clock, FontDriver
from unicornclock.animations import ClockAnimationMixin
from unicornclock.brightness import Brightness


try:
    from secrets import WLAN_SSID, WLAN_PASSWORD
except ImportError:
    print("Create secrets.py with WLAN_SSID and WLAN_PASSWORD information.")
    raise


rtc = machine.RTC()

# overclock to 200Mhz
machine.freq(200000000)

# create galactic object and graphics surface for drawing
galactic = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY_GALACTIC_UNICORN)

WHITE = graphics.create_pen(255, 255, 255)
BLACK = graphics.create_pen(0, 0, 0)
SKYBLUE = graphics.create_pen(52, 232, 235)
PURPLE = graphics.create_pen(143, 52, 235)
GREY = graphics.create_pen(100, 100, 100)
RED = graphics.create_pen(255, 0, 0)


def wlan_connection():
    x = 0
    def wait():
        nonlocal x
        graphics.set_pen(RED)
        graphics.pixel(x, 0)
        galactic.update(graphics)
        x += 1

    wait()

    sta_if = network.WLAN(network.STA_IF)

    if not sta_if.isconnected():
        print('Connecting to %s network...' % WLAN_SSID)
        sta_if.active(True)
        sta_if.connect(WLAN_SSID, WLAN_PASSWORD)

        while not sta_if.isconnected():
            wait()
            sleep(0.5)

    print('Connected to %s network' % WLAN_SSID)
    print('Network config:', sta_if.ifconfig())

    graphics.set_pen(BLACK)
    graphics.clear()

    ntptime.settime()


class ExampleClockNoSpace(ClockAnimationMixin, Clock):
    """ExampleClockNoSpace

    Example of clock:
    - Animated
    - Without space between each characters
    - The color of each char is set in the callback_text_write_char method
    """
    space_between_char = 0

    def callback_text_write_char(self, char, index):
        colors = [
            GREY, WHITE,
            RED,
            GREY, WHITE,
            RED,
            GREY, WHITE,
        ]
        graphics.set_pen(colors[index])


async def brightness_handler():
    brightness = Brightness(galactic, offset=20)
    while True:
        brightness.update()
        await asyncio.sleep(1)


async def example():
    clock = ExampleClockNoSpace(
        galactic,
        graphics,
        x=-1,   # Right align
        show_seconds=True,
        am_pm_mode=False,
        utc_offset=2,
    )

    asyncio.create_task(brightness_handler())
    asyncio.create_task(clock.run())


def main():
    wlan_connection()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
    loop.run_forever()


if __name__ == '__main__':
    main()