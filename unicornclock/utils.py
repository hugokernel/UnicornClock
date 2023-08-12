import machine
import math
import ntptime
import time


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


@micropython.native  # noqa: F821
def from_hsv(h, s, v):
    i = math.floor(h * 6.0)
    f = h * 6.0 - i
    v *= 255.0
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

    i = int(i) % 6
    if i == 0:
        return int(v), int(t), int(p)
    if i == 1:
        return int(q), int(v), int(p)
    if i == 2:
        return int(p), int(v), int(t)
    if i == 3:
        return int(p), int(q), int(v)
    if i == 4:
        return int(t), int(p), int(v)
    if i == 5:
        return int(v), int(p), int(q)


def set_time(rtc, utc_offset=0):
    # There is no timezone support in Micropython,
    # we need to use tricks

    rtc = machine.RTC()

    ntptime.settime()

    y, mo, d, wd, h, m, s, ss = rtc.datetime()
    mktime = time.mktime((y, mo, d, h, m, s, wd, None))

    mktime += utc_offset * 3600

    y, mo, d, h, m, s, _, _ = time.localtime(mktime)

    rtc.datetime((y, mo, d, wd, h, m, s, ss))
