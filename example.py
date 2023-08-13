import machine
import network
import uasyncio as asyncio
from galactic import GalacticUnicorn
from machine import Pin
from picographics import DISPLAY_GALACTIC_UNICORN, PicoGraphics
from time import sleep

from unicornclock import Brightness, Clock, Position
from unicornclock.effects import (
    CharacterSlideDownEffect,
    RainbowCharEffect,
    RainbowPixelEffect,
    RainbowMoveEffect,
)
from unicornclock.utils import debounce, set_time
from unicornclock.widgets import Calendar


try:
    from secrets import WLAN_SSID, WLAN_PASSWORD
except ImportError:
    print("Create secrets.py with WLAN_SSID and WLAN_PASSWORD information.")
    raise

# overclock to 200Mhz
machine.freq(200000000)

# create galactic object and graphics surface for drawing
galactic = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY_GALACTIC_UNICORN)

WHITE = graphics.create_pen(255, 255, 255)
BLACK = graphics.create_pen(0, 0, 0)
GREY = graphics.create_pen(100, 100, 100)
RED = graphics.create_pen(255, 0, 0)


UTC_OFFSET = 2


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


class NoSpaceClock(Clock):
    space_between_char = lambda _, index, char: 1 if index in (0, 3, 6) else 0


class SimpleClock(NoSpaceClock):

    def callback_write_char(self, char, index):
        colors = [
            GREY, WHITE,
            RED,
            GREY, WHITE,
            RED,
            GREY, WHITE,
        ]
        graphics.set_pen(colors[index])


class RainbowCharEffectClock(
    RainbowCharEffect,
    CharacterSlideDownEffect,
    NoSpaceClock,
):
    pass


class RainbowPixelEffectClock(
    RainbowPixelEffect,
    CharacterSlideDownEffect,
    NoSpaceClock,
):
    pass


class RainbowMoveEffectClock(RainbowMoveEffect, NoSpaceClock):
    pass


examples = [
    SimpleClock,
    RainbowCharEffectClock,
    RainbowPixelEffectClock,
    RainbowMoveEffectClock,
]

def get_example(index):
    return examples[index]


async def buttons_handler(brightness, clock, calendar, update_calendar):

    clock_on_the_right = False

    example_index = 0

    def clear():
        graphics.remove_clip()
        graphics.set_pen(BLACK)
        graphics.clear()

    @debounce()
    def switch_position(p):
        nonlocal clock_on_the_right

        clear()

        clock.set_position(
            Position.RIGHT if clock_on_the_right else Position.LEFT
        )
        calendar.set_position(
            Position.LEFT if clock_on_the_right else Position.RIGHT
        )
        clock.full_update()
        calendar.draw_all()
        clock_on_the_right = not clock_on_the_right

    def load_example():
        nonlocal clock

        clear()

        clock.is_running = False

        clock = get_example(example_index % len(examples))(
            galactic,
            graphics,
            x=Position.RIGHT,
            show_seconds=True,
            am_pm_mode=False,
            callback_hour_change=update_calendar,
        )

        asyncio.create_task(clock.run())

    @debounce()
    def switch_example(p):
        nonlocal example_index

        example_index += 1

        load_example()

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

    Pin(GalacticUnicorn.SWITCH_B, Pin.IN, Pin.PULL_UP) \
        .irq(trigger=Pin.IRQ_FALLING, handler=switch_example)

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

    clock = get_example(0)(
        galactic,
        graphics,
        x=Position.RIGHT,
        show_seconds=True,
        am_pm_mode=False,
        callback_hour_change=update_calendar,
    )

    asyncio.create_task(buttons_handler(brightness, clock, calendar,
                                        update_calendar))
    asyncio.create_task(brightness.run())
    asyncio.create_task(clock.run())


def main():
    wlan_connection()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
    loop.run_forever()


if __name__ == '__main__':
    main()