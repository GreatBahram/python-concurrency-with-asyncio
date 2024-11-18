import asyncio
import functools
import time
from typing import Any, Callable


def async_timed():
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            print(f"Starting {func} with args {args} {kwargs}")
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed_time = time.time() - start_time
                print(f"finsihed {func} in {elapsed_time:.4f} second(s)")

        return wrapped

    return wrapper


@async_timed()
async def delay(seconds: int) -> int:
    print(f"Sleeping for {seconds} seconds.")
    await asyncio.sleep(seconds)
    print(f"Finished sleeping for {seconds} seconds.")
    return seconds
