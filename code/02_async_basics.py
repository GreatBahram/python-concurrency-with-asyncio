import asyncio
from typing import Any, Callable
from utils.delay import delay
import asyncio
from asyncio import CancelledError
from asyncio import Future
import time
import requests


# part 01: introducing coroutine
async def coroutine_add_one(number: int) -> int:
    return number + 1


def add_one(number: int) -> int:
    return number + 1


function_result = add_one(1)
coroutine_result = coroutine_add_one(1)
print(f"Function result is {function_result} and the type is {type(function_result)}")
print(
    f"Coroutine result is {coroutine_result} and the type is {type(coroutine_result)}"
)


# part 02: how to run a coroutine?


async def coroutine_add_one(number: int) -> int:
    return number + 1


result = asyncio.run(coroutine_add_one(1))
print(result)


# part 03: the issue with a simpel await


async def add_one(number: int) -> int:
    return number + 1


async def main() -> None:
    one_plus_one = await add_one(1)
    two_plus_one = await add_one(2)
    print(one_plus_one)
    print(two_plus_one)


asyncio.run(main())


# part 04: is it truly asynchronous


async def hello_world_msg() -> str:
    await asyncio.sleep(1)
    return "Hello, World!"


async def main() -> None:
    msg = await hello_world_msg()
    print(msg)


asyncio.run(main())


# part 05


async def add_one(number: int) -> int:
    return number + 1


async def hello_world_message() -> str:
    await delay(1)
    return "Hello World!"


async def main() -> None:
    message = await hello_world_message()
    one_plus_one = await add_one(1)
    print(one_plus_one)
    print(message)


asyncio.run(main())


# part 06: introducing the delay function
async def delay(seconds: int) -> None:
    print(f"Sleeping for {seconds} seconds.")
    await asyncio.sleep(seconds)
    print(f"Finished sleeping for {seconds} seconds.")
    return seconds


async def main() -> None:
    sleep = asyncio.create_task(delay(5))
    print(type(sleep))
    result = await sleep
    print(result)


asyncio.run(main())


# part 07: how to create tasks?
async def delay(seconds: int) -> None:
    print(f"Sleeping for {seconds} seconds.")
    await asyncio.sleep(seconds)
    print(f"Finished sleeping for {seconds} seconds.")
    return seconds


async def main() -> None:
    sleep1 = asyncio.create_task(delay(5))
    sleep2 = asyncio.create_task(delay(7))
    sleep3 = asyncio.create_task(delay(6))
    await sleep1
    await sleep2
    await sleep3


asyncio.run(main())


# part 01: cancelling a task


async def main():
    long_task = asyncio.create_task(delay(10))
    seconds_elapsed = 0

    while not long_task.done():
        print("Task not finished, checking again in a second.")
        await asyncio.sleep(1)
        seconds_elapsed = seconds_elapsed + 1
        if seconds_elapsed == 5:
            long_task.cancel()
        try:
            await long_task
        except CancelledError:
            print("Our task was cancelled")


asyncio.run(main())


# part 09: timeout a coroutine: cancelling a task is boring, let's do a timeout instead!


async def main():
    delay_task = asyncio.create_task(delay(2))
    try:
        result = await asyncio.wait_for(delay_task, timeout=1)
        print(result)
    except asyncio.exceptions.TimeoutError:
        print("Got a timeout!")
        print(f"Was the task cancelled? {delay_task.cancelled()}")


asyncio.run(main())


# part 10: shielding a coroutine
# this is a neat feature;


async def main():
    task = asyncio.create_task(delay(10))
    try:
        result = await asyncio.wait_for(asyncio.shield(task), 5)
        print(result)
    except TimeoutError:
        print("Task took longer than five seconds, it will finish soon!")
        result = await task
        print(result)


asyncio.run(main())


# part 11: task vs coroutine vs future
# Future is going to have a value in future; and we can also set either the value or the exception
# JFYI, Future is also awaitable
# let's demonstrate this


def make_request() -> Future:
    future = Future()
    asyncio.create_task(set_future_value(future))
    return future


async def set_future_value(future: Future) -> None:
    await asyncio.sleep(1)
    future.set_result(42)


async def main() -> None:
    future = make_request()
    print(f"Is future value set {future.done()}")
    value = await future
    print(f"Is future value set {future.done()}")
    print(f"{value=}")


asyncio.run(main())

# part 12: measure how much time has elapsed.


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


@async_timed
async def delay(): ...


@async_timed
async def main():
    task1 = asyncio.create_task(delay(2))
    task2 = asyncio.create_task(delay(3))

    await task1
    await task2


asyncio.run(main())


# Part 13: Why asyncio is not good for cpu-bound task?
# Here we want to demonstrate this one more time.
# The way we show this is that even though we create two tasks,
# each should finish then the other one can begin!!!


@async_timed
async def cpu_bound_task():
    """
    NOTE: There is not a single 'await' in this funciton!
    """
    counter = 0

    for i in range(100_000_000):
        counter += 1

    return counter


@async_timed
async def main():
    cpu_task1 = asyncio.create_task(cpu_bound_task())
    cpu_task2 = asyncio.create_task(cpu_bound_task())
    await cpu_task1
    await cpu_task2


# Part 14: running blockin API
# Here is the same shit, you can't download a file faster using asyncio + requests
# that library should also act like a coroutine


@async_timed
async def get_example_status() -> int:
    # NOTE: please understand requests is a sync library.
    return requests.get("https://example.com").status_code


@async_timed
async def main():
    task1 = asyncio.create_task(get_example_status())
    task2 = asyncio.create_task(get_example_status())

    await task1
    await task2


asyncio.run(main())


# Part 15: who controls the left, controls the world!
# with this approach we create a new event loop


async def main():
    await asyncio.sleep(1)


loop = asyncio.new_event_loop()

try:
    loop.run_until_complete(main())
finally:
    loop.close()


# NOTE: we can also access the current event loop


def coroutine():
    print("Hallo")


async def main():
    loop = asyncio.get_event_loop()
    loop.call_soon(
        coroutine
    )  # NOTE: here we should pass a callabe and it should be synchronous function; otherwise
    # stick to create_task method of asyncio.
    await asyncio.sleep(2)


asyncio.run(main())

# part 16: debug mode
# There are a few ways to activate this:
asyncio.run(main(), debug=True)
# python3 -X dev main.py
# env variable 🤷
# PYTHONASYINCIODEBUG=1 python3 program.py

# Test program: Here you will see a nice message that cpu_bound_task is taking a hell of time.


async def cpu_bound_task():
    counter = 0

    for i in range(10_000_000):
        counter += 1

    return counter


async def main():
    cpu_task1 = asyncio.create_task(cpu_bound_task())
    await cpu_task1


asyncio.run(main())
