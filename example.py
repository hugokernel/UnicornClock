import machine
import network
import ntptime
import time
import uasyncio as asyncio
from galactic import GalacticUnicorn
from machine import Pin
from picographics import DISPLAY_GALACTIC_UNICORN, PicoGraphics
from time import sleep

from unicornclock import Brightness, Clock, Position
from unicornclock.animations import CharacterSlideDownAnimation
from unicornclock.widgets import Calendar


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


UTC_OFFSET = 2


def set_time(utc_offset=0):
    # There is no timezone support in Micropython,
    # we need to use tricks

    ntptime.settime()

    y, mo, d, wd, h, m, s, ss = rtc.datetime()
    mktime = time.mktime((y, mo, d, h, m, s, wd, None))

    mktime += utc_offset * 3600

    y, mo, d, h, m, s, _, _ = time.localtime(mktime)

    rtc.datetime((y, mo, d, wd, h, m, s, ss))


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

    set_time(UTC_OFFSET)


def debounce(ms=250):
    """Button debounce

    The args `ms` is the delay in milliseconds below which
    the function call is ignored.
    """
    timeout = time.ticks_ms()

    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal timeout

            if time.ticks_diff(time.ticks_ms(), timeout) < ms:
                return

            func(*args, **kwargs)

            timeout = time.ticks_ms()
        return wrapper

    return decorator


class ExampleClockNoSpace(CharacterSlideDownAnimation, Clock):
#class ExampleClockNoSpace(Clock):
    """ExampleClockNoSpace

    Example of clock:
    - Animated
    - Without space between each characters
    - The color of each char is set in the callback_write_char method
    """

    space_between_char = lambda _, index, char: 1 if index in (0, 3, 6) else 0

    def callback_write_char(self, char, index):
        colors = [
            GREY, WHITE,
            RED,
            GREY, WHITE,
            RED,
            GREY, WHITE,
        ]
        graphics.set_pen(colors[index])


async def buttons_handler(brightness, clock, calendar):

    clock_on_the_right = False

    @debounce()
    def switch_position(p):
        nonlocal clock_on_the_right

        graphics.remove_clip()
        graphics.set_pen(BLACK)
        graphics.clear()

        clock.set_position(
            Position.RIGHT if clock_on_the_right else Position.LEFT
        )
        calendar.set_position(
            Position.LEFT if clock_on_the_right else Position.RIGHT
        )
        clock.full_update()
        calendar.draw_all()
        clock_on_the_right = not clock_on_the_right

    @debounce()
    def brightness_down(p):
        brightness.adjust(-5)
        brightness.update()

    @debounce()
    def brightness_up(p):
        brightness.adjust(5)
        brightness.update()

    Pin(GalacticUnicorn.SWITCH_A, Pin.IN, Pin.PULL_UP) \
        .irq(trigger=Pin.IRQ_FALLING, handler=switch_position)

    Pin(GalacticUnicorn.SWITCH_BRIGHTNESS_DOWN, Pin.IN, Pin.PULL_UP) \
        .irq(trigger=Pin.IRQ_FALLING, handler=brightness_down)

    Pin(GalacticUnicorn.SWITCH_BRIGHTNESS_UP, Pin.IN, Pin.PULL_UP) \
        .irq(trigger=Pin.IRQ_FALLING, handler=brightness_up)

    while True:
        await asyncio.sleep(0.25)


async def example():
    brightness = Brightness(galactic, offset=20)

    calendar = Calendar(galactic, graphics)

    def update_calendar(*args):
        calendar.draw_all()

    clock = ExampleClockNoSpace(
        galactic,
        graphics,
        x=Position.RIGHT,
        show_seconds=True,
        am_pm_mode=False,
        callback_hour_change=update_calendar,
    )

    asyncio.create_task(buttons_handler(brightness, clock, calendar))
    asyncio.create_task(brightness.run())
    asyncio.create_task(clock.run())


def main():
    wlan_connection()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
    loop.run_forever()


if __name__ == '__main__':
    main()