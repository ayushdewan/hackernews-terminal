import time
from functools import wraps
from threading import Lock


def throttle(rate_limit):
    """A decorator to limit function calls to a specified rate per second."""
    interval = 1.0 / rate_limit

    def decorator(func):
        lock = Lock()
        last_time = 0.0

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_time
            with lock:
                now = time.monotonic()
                elapsed = now - last_time
                wait = interval - elapsed
                if wait > 0:
                    time.sleep(wait)
                last_time = time.monotonic()
            result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator
