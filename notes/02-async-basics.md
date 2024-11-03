## Introducing coroutines

Think of a coroutine like a regular Python function but with the superpower that it can pause its execution when it encounters an operation that could take a while to complete. While a paused coroutine is waiting for the operation it paused for to finish, we can run other code. 

This running of other code while waiting is what gives our application concurrency.

To both create and pause a coroutine, we’ll need to learn to use Python’s `async` and `await` keywords. 

The `async` keyword will let us define a coroutine; the `await` keyword will let us pause our coroutine when we have a long-running operation.

> [!NOTE]
>
> `await` can only be used inside a coroutine.

```python
async def my_coroutine() -> None
    print("Hello world!")
```



```python
async def coroutine_add_one(number: int) -> int:
    return number + 1

def add_one(number: int) -> int:
    return number + 1

function_result = add_one(1)
coroutine_result = coroutine_add_one(1)
print(f'Function result is {function_result} and the type is {type(function_result)}')
print(f'Coroutine result is {coroutine_result} and the type is
{type(coroutine_result)}'
```

> [!TIP]
>
> Here, we tried to run a coroutine, but we don't have the result. since we can't run a coroutine like as a normal function.

## How to run a coroutine?

There is when event loop comes into the picture, one simple solution:

```python
import asyncio
import functools
from typing import Any, Callable


async def coroutine_add_one(number: int) -> int:
    return number + 1


result = asyncio.run(coroutine_add_one(1))
print(result)
```

`asyncio.run` seems like a good option to pass a function that includes all other coroutines, what do you think?

```python
async def add_one(number: int) -> int:
    return number + 1


async def main() -> None:
    one_plus_one = await add_one(1)
    two_plus_one = await add_one(2)
    print(one_plus_one)
    print(two_plus_one)


asyncio.run(main())
```

## Asynchronous sleeping

Let's assume we have a long-running coroutine, how do we run this? We can't just run the `time.sleep` since that is a synchronous function, that's the thing, in async world, everything should be async, otherwise we are not benefiting that much.

```python
import asyncio


async def hello_world_msg() -> str:
    await asyncio.sleep(1)
    return "Hello, World!"


async def main() -> None:
    msg = await hello_world_msg()
    print(msg)


asyncio.run(main())
```



Calling `asyncio.sleep` seems tedious, we can do better, right?



```python
import asyncio
from utils import delay


async def delay(seconds: int) -> None:
    print(f"Sleeping for {seconds} seconds.")
    await asyncio.sleep(seconds)
    print(f"Finished sleeping for {seconds} seconds.")
    return seconds

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
```

## Is it truly asynchronous?

Wait a minute, are we truly benefiting from async stuff, as everything here runs sequentially, 🤔

Task comes into the picture, 🎉, we create tasks, and event loop promises to run them asap; event loop runs the tasks as soon as we hit the first await keyword.

```python
import asyncio


async def main() -> None:
    sleep = asyncio.create_task(delay(5))
    print(type(sleep))
    result = await sleep
    print(result)


asyncio.run(main())
```

```python
async def delay(seconds: int) -> None:
    print(f"Sleeping for {seconds} seconds.")
    await asyncio.sleep(seconds)
    print(f"Finished sleeping for {seconds} seconds.")
    return seconds


import asyncio


async def main() -> None:
    sleep1 = asyncio.create_task(delay(5))
    sleep2 = asyncio.create_task(delay(7))
    sleep3 = asyncio.create_task(delay(6))
    await sleep1
    await sleep2
    await sleep3


asyncio.run(main())
```

But let's demonstrate that we are enjoying our time, here:

```python
async def other_job():
    for _ in range(2):
        await asyncio.sleep(1)
        print("Doing other stuff")


async def delay(seconds: int) -> None:
    print(f"Sleeping for {seconds} seconds.")
    await asyncio.sleep(seconds)
    print(f"Finished sleeping for {seconds} seconds.")
    return seconds


import asyncio


async def main() -> None:
    sleep1 = asyncio.create_task(delay(5))
    sleep2 = asyncio.create_task(delay(7))
    await other_job()
    await sleep1
    await sleep2


asyncio.run(main())
```

## Stop a task

Running coroutine is great and all, but how can we stop these shits?

There are two main ways to do so:

- canceling

  ```python
  import asyncio
  from asyncio import CancelledError
  
  
  async def delay(seconds: int) -> None:
      print(f"Sleeping for {seconds} seconds.")
      await asyncio.sleep(seconds)
      print(f"Finished sleeping for {seconds} seconds.")
      return seconds
  
  
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
  ```

  Counting the time is a not the best task to do in this world, there must be a better way.

- timeouting

  ```python
  # part 10: timeout a coroutine: cancelling a task is boring, sicne we need to watch how many seconds have bee passed!
  
  import asyncio
  
  
  async def delay(seconds: int) -> None:
      print(f"Sleeping for {seconds} seconds.")
      await asyncio.sleep(seconds)
      print(f"Finished sleeping for {seconds} seconds.")
      return seconds
  
  
  async def main():
      delay_task = asyncio.create_task(delay(2))
      try:
          result = await asyncio.wait_for(delay_task, timeout=1)
          print(result)
      except asyncio.exceptions.TimeoutError:
          print("Got a timeout!")
          print(f"Was the task cancelled? {delay_task.cancelled()}")
  
  
  asyncio.run(main())
  ```

  To make a bit weird, there is also another approach, shielding

  ```python
  # part 10: shielding a coroutine
  # this could be a neat feature;
  # we need we have waited more than we should and then we can make a decision based on user input
  
  import asyncio
  
  
  async def delay(seconds: int) -> None:
      print(f"Sleeping for {seconds} seconds.")
      await asyncio.sleep(seconds)
      print(f"Finished sleeping for {seconds} seconds.")
      return seconds
  
  
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
  ```

## Terminology

Let's ponder for a second, now we have three different terminology:

- coroutine
- Task
- Future

```python

# part 11: task vs coroutine vs future
from asyncio import Future
# Future is going to have a value in future; and we can also set either the value or the exception
# JFYI, Future is also awaitable
# let's demonstrate this

from asyncio import Future


def make_request() -> Future:
    # NOTE: we made this fuction sync?
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
```

## Elapsed Time

Let's implement something so we can track how much time each coroutine is taking

```python
# part 12: measure how much time has elapsed.
import time


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
```

Let's demonstrate it:

```python
# example for the async_timed
# TODO: here it would nice to have two different task, each waits for different time
# the output shows one more time that coroutine do not run sequentially.

@async_timed
async def delay():
    pass


@async_timed
async def main():
    task1 = asyncio.create_task(delay(2))
    task2 = asyncio.create_task(delay(3))

    await task1
    await task2

asyncio.run(main())
```

## Don't make eveything async

Wow, `async` is so nice, that I like to make everything `async`, what about you? Nope, you shouldn't two things you shouldn't make async

- cpu bound task

  ```python
  # Part 13: Why asyncio is not good for cpu-bound task?
  # Here we want to demonstrate this one more time.
  # The way we show this is that even though we create two tasks,
  # each should finish then the other one can begin!!!
  
  
  @async_timed
  async def cpu_bound_task():
      """
      NOTE: There is single await in this funciton!
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
  asyncio.run(main())
  ```

- blocking things

  ```python
  
  # Part 14: running blockin API
  # Here is the same shit, you can't download a file faster using asyncio + requests
  # that library should also act like a coroutine
  
  import requests
  
  
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
  ```

So far, we did stick to a very simple endpoint from asyncio, `asyncio.run`, but there are other ways too:

- creating a new event loop

  ```python
  
  # Part 15: who controls the left, controls the world!
  # with this approach we create a new event loop
  async def main():
      await asyncio.sleep(1)
  
  
  loop = asyncio.new_event_loop()
  
  try:
      loop.run_until_complete(main())
  finally:
      loop.close()
  ```

  

- get the current event loop and do something with it

  ```python
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
  ```



## Debug mode

There are many ways, including

- kindly, asking the event loop while creating it.
- run the interpreter with a feature flag `-X dev`



```python
# part 16: debug mode
# There are a few ways to activate this:
asyncio.run(main(), debug=True)
# python3 -X dev main.py
# env variable 🤷
# PYTHONASYINCIODEBUG=1 python3 program.py

# Test program: Here you will see a nice message that cpu_bound_task is taking a hell of time.
import asyncio


async def cpu_bound_task():
    counter = 0

    for i in range(10_000_000):
        counter += 1

    return counter


async def main():
    cpu_task1 = asyncio.create_task(cpu_bound_task())
    await cpu_task1


asyncio.run(main())

```
