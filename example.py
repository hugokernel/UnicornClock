import json
import machine
import network
import time
import uasyncio as asyncio
from galactic import GalacticUnicorn
from machine import Pin
from picographics import DISPLAY_GALACTIC_UNICORN, PicoGraphics

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

BLACK = graphics.create_pen(0, 0, 0)
BLUE = graphics.create_pen(0, 0, 255)
GREEN = graphics.create_pen(0, 255, 0)
GREY = graphics.create_pen(100, 100, 100)
ORANGE = graphics.create_pen(255, 128, 0)
RED = graphics.create_pen(255, 0, 0)
WHITE = graphics.create_pen(255, 255, 255)


UTC_OFFSET = 2

SETTINGS_FILE = 'demo.json'


def wlan_connection():
    """WLAN connection

    During the connection, a colored progress is displayed.

    Color signification:
    - RED: Starting the connection
    - BLUE: Waiting for WLAN connection
    - ORANGE: Waiting for NTP update
    - GREEN: Done
    """
    width, height = graphics.get_bounds()

    x = 0
    def wait(color):
        nonlocal x
        graphics.set_pen(color)
        graphics.rectangle(x, 0, 2, height)
        galactic.update(graphics)
        x += 2
        if x >= width:
            x = 0
            graphics.set_pen(BLACK)
            graphics.clear()

    wait(RED)

    sta_if = network.WLAN(network.STA_IF)

    if not sta_if.isconnected():
        print('Connecting to %s network...' % WLAN_SSID)
        sta_if.active(True)
        sta_if.connect(WLAN_SSID, WLAN_PASSWORD)

        while not sta_if.isconnected():
            wait(BLUE)
            time.sleep(0.25)

    print('Connected to %s network' % WLAN_SSID)
    print('Network config:', sta_if.ifconfig())

    wait(ORANGE)

    set_time(UTC_OFFSET)

    wait(GREEN)

    graphics.set_pen(BLACK)
    graphics.clear()


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


effects = [
    SimpleClock,
    RainbowCharEffectClock,
    RainbowPixelEffectClock,
    RainbowMoveEffectClock,
]

clock = None

async def load_example(effect_index, **kwargs):
    global clock

    if clock:
        clock.is_running = False

    graphics.remove_clip()
    graphics.set_pen(BLACK)
    graphics.clear()

    default_kwargs = {
        'x': Position.RIGHT,
        'show_seconds': True,
        'am_pm_mode': False,
    }

    if kwargs:
        default_kwargs.update(kwargs)

    clock = effects[effect_index](
        galactic,
        graphics,
        **default_kwargs,
    )

    asyncio.create_task(clock.run())

mode = 0
effect = 0

try:
    print('Restoring the settings...', end='')
    with open(SETTINGS_FILE, 'r') as f:
        d = json.loads(f.read())
except (OSError, ValueError):
    print('[ERROR]')
else:
    mode = d.get('mode', 0)
    effect = d.get('effect', 0)
    print('[OK]')


async def buttons_handler(brightness, calendar, update_calendar):
    clock_kwargs = {}

    @debounce()
    def switch_mode(p):
        global mode
        mode = (mode + 1) % 4

    @debounce()
    def switch_effect(p):
        global effect
        effect = (effect + 1) % len(effects)

    @debounce()
    def brightness_down(p):
        brightness.adjust(-5)
        brightness.update()

    @debounce()
    def brightness_up(p):
        brightness.adjust(5)
        brightness.update()

    Pin(GalacticUnicorn.SWITCH_A, Pin.IN, Pin.PULL_UP) \
        .irq(trigger=Pin.IRQ_FALLING, handler=switch_mode)

    Pin(GalacticUnicorn.SWITCH_B, Pin.IN, Pin.PULL_UP) \
        .irq(trigger=Pin.IRQ_FALLING, handler=switch_effect)

    Pin(GalacticUnicorn.SWITCH_BRIGHTNESS_DOWN, Pin.IN, Pin.PULL_UP) \
        .irq(trigger=Pin.IRQ_FALLING, handler=brightness_down)

    Pin(GalacticUnicorn.SWITCH_BRIGHTNESS_UP, Pin.IN, Pin.PULL_UP) \
        .irq(trigger=Pin.IRQ_FALLING, handler=brightness_up)

    current_effect = 0
    current_mode = 0
    last_change_time = None
    while True:
        if mode != current_mode or effect != current_effect:
            print('Change (mode %i, effect %i)' % (mode, effect))

            if mode == 0:
                calendar.set_position(Position.LEFT)
                clock_kwargs = {
                    'x': Position.RIGHT,
                    'callback_hour_change': update_calendar,
                }
            elif mode == 1:
                calendar.set_position(Position.RIGHT)
                clock_kwargs = {
                    'x': Position.LEFT,
                    'callback_hour_change': update_calendar,
                }
            elif mode == 2:
                clock_kwargs = {
                    'x': Position.CENTER,
                    'callback_hour_change': None,
                    'space_between_char': 2,
                }
            elif mode == 3:
                clock_kwargs = {
                    'show_seconds': False,
                    'x': Position.CENTER,
                    'callback_hour_change': None,
                    'space_between_char': 2,
                }

            await load_example(effect, **clock_kwargs)

            current_mode = mode
            current_effect = effect

            last_change_time = time.time()

        if last_change_time and last_change_time + 5 < time.time():
            print('Saving the settings file')
            with open(SETTINGS_FILE, 'w') as f:
                f.write(json.dumps({'mode': mode, 'effect': effect}))

            last_change_time = None

        await asyncio.sleep(0.25)


async def example():
    brightness = Brightness(galactic, offset=20)
    brightness.update()

    wlan_connection()

    calendar = Calendar(galactic, graphics)

    def update_calendar(*args):
        calendar.draw_all()

    asyncio.create_task(brightness.run())
    asyncio.create_task(buttons_handler(brightness, calendar, update_calendar))

    await load_example(0, callback_hour_change=update_calendar)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
    loop.run_forever()


if __name__ == '__main__':
    main()