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
