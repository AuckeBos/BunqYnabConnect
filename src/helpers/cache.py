import shelve
from functools import wraps
from time import time
import os

def cache(ttl: int = None):
    """
    Cache decorator, to cache the result of a function for some seconds
    :param ttl: Time to live of cache in seconds
    args
    """
    expires_at = time() + ttl

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args[1:]) + str(tuple(sorted(kwargs.items())))[1:-1]
            c = shelve.open(
                f"{os.path.dirname(__file__)}/../../cache/{func.__name__}_{key}"
            )
            is_expired = (
                "expires_at" in c
                and c["expires_at"] is not None
                and c["expires_at"] < time()
            )
            cache_valid = not is_expired and "value" in c
            if not cache_valid:
                value = func(*args, **kwargs)
                c["value"] = value
                c["expires_at"] = expires_at
            else:
                value = c["value"]
            c.close()
            return value

        return wrapper

    return decorator
