# Concurrent web requests

Using `asyncio` with the `aiohttp` library enables making hundreds of web requests simultaneously, significantly reducing runtime compared to synchronous methods.

`aiohttp` uses <u>non-blocking sockets</u> to handle requests as coroutines, which we can await for results.

We'll also explore running multiple coroutines concurrently, with strategies like:

- Waiting for all tasks to complete.
- Processing results as they arrive.

# asyncio-friendly library

Here, we're gonna use `aiohttp` as the `requests` library uses <u>blocking-sockets</u>. To address this issue and get concurrency, we need to use a library that is <u>non-blocking</u> all the way down to the socket layer.

## Asynchronous context manager

```python
def main():
    fp = open("alaki.txt")
    try:
        data = fp.readlines()
    finally:
        fp.close()

    with open("alaki.txt") as fp:
        data = fp.readlines()
```

In case you're not familiar with context manager check [this blog post](https://virgool.io/@GreatBahram/once-for-ever-context-manager-qqqbqxgryxk5). Python introduced a new language feature to support this use case, called asynchronous context managers, `__aenter_`, `__aexit__`.

```python
class ConnectedSocket:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.conn = None

    async def __aenter__(self) -> socket.socket:
        loop = asyncio.get_event_loop()
        print("Entering context manager, waiting for connection")
        conn, addr = await loop.sock_accept(self.sock)
        print("Accepted a connection")
        self.conn = conn
        return self.conn

    async def __aexit__(self, *args):
        print("Exiting context manager")
        self.conn.close()
        print("Closed connection")

        

async def main() -> None:
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    address = ("localhost", 8000)
    server_sock.setblocking(False)
    server_sock.bind(address)
    server_sock.listen()
    loop = asyncio.get_event_loop()
    async with ConnectedSocket(server_sock) as conn:
        data = await loop.sock_recv(conn, 1024)
        print(f"Got data: {data}")
        

asyncio.run(main())

```

With a session, you’ll keep many connections open, which can then be recycled. This is known as connection pooling. We can create a session by using `async with` syntax and the `aiohttp.ClientSession` asynchronous context manager.

```python
import aiohttp


async def fetch_status(session: aiohttp.ClientSession, url: str) -> int:
    async with session.get(url) as resp:
        return resp.status


async def main():
    async with aiohttp.ClientSession() as session:
        status = await fetch_status(session, "https://example.com")
        print(f"{status=}")


asyncio.run(main())
```

Note that a `ClientSession` will create a default maximum of 100 connections by default.

### Running tasks concurrently

```python
from code.utils import delay, async_timed


async def main():
    # conventional approach
    t1 = asyncio.create_task(delay(1))
    t2 = asyncio.create_task(delay(2))
    t3 = asyncio.create_task(delay(3))

    await t1
    await t2
    await t3


asyncio.run(main())
```

Imagine you have hundreds, thousands, or even more web requests concurrently, this style would become
verbose and messy!

One could use this ugly method, however this means that we pause the list comprehension and the main coroutine for every delay task we create until that delay task completes.

```python
from code.utils import delay, async_timed


async def main():
    # a new ugly approach
    delay_times = [1, 2, 3]
    [await asyncio.create_task(delay(seconds)) for seconds in delay_times]


asyncio.run(main())
```

Below you find another ugly approach, while this approach addresses the issue, we are abusing list-comprehension and we don't wanna do that, right? Another disadvantage is that we can't process the tasks as soon as they're ready.

```python
from code.utils import delay, async_timed


async def main():
    # a tricky approach
    delay_times = [1, 2, 3]
    tasks = [asyncio.create_task(delay(seconds)) for seconds in delay_times]
    [await t for t in tasks]


asyncio.run(main())
```

### Meet the lifesaver 🎉

`asyncio` offers a method, called `gather` takes in a sequence of awaitables and lets us run them con-
currently, all in one line of code 🤯 and it returns an awaitable

```python
async def fetch_status(session: aiohttp.ClientSession, url: str) -> int:
    async with session.get(url) as resp:
        return resp.status

    
async def main():
    async with aiohttp.ClientSession() as session:
        requests = [fetch_status(session, "https://example.com") for _ in range(1_000)]
        status_codes = await asyncio.gather(*requests)
        print(status_codes)
```

Let's compare this with a synchronous app 🤔:

```python
from code.utils import delay, async_timed


async def fetch_status(session: aiohttp.ClientSession, url: str) -> int:
    async with session.get(url) as resp:
        return resp.status

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        status_codes = [await fetch_status(session, "https://example.com") for _ in range(50)]
        print(status_codes)
```

A nice feature of gather is that, regardless of when our awaitables complete, we are guaranteed the results will be returned in the order we passed them in.

```python
from code.utils import delay, async_timed



async def main():
    tasks = [delay(3), delay(1)]
    results = await asyncio.gather(*tasks)
    print(results)
```

Exception handing in `asyncio.gather` using `return_exceptions`

```python
async def main():
    async with aiohttp.ClientSession() as session:
        requests = [
            fetch_status(session, "https://example.com"),
            fetch_status(session, "python://example.com"),
        ]
        status_codes = await asyncio.gather(*requests)
        print(status_codes)
```

let's set it to True and see what happens:

```python
async def main():
    async with aiohttp.ClientSession() as session:
        requests = [
            fetch_status(session, "https://example.com"),
            fetch_status(session, "python://example.com"),
        ]
        status_codes = await asyncio.gather(*requests, return_exceptions=True)
        print(status_codes)
```

still `asyncio.gather` has a few drawbacks:

- You can cancel the rest of the tasks if one fails
- Secondly, we need to make sure all awaitables are finished.

There must be a better way 🤔 ...

## Second savior - `as_completed`

To overcome this issue, asyncio exposes as_completed function, that takes a list of awaitables and returns an iterator of futures. And most definitely the result can't be deterministic.

```python
import asyncio
from code.utils import delay, async_timed


async def main():
    delay_times = [1, 2, 3]
    tasks = [asyncio.create_task(delay(seconds)) for seconds in delay_times]
    for finished_task in asyncio.as_completed(*tasks):
        result = await finished_task
        print(f"{result=})


asyncio.run(main())
```

## True savior - `wait`

`asyncio.wait` returns two sets one for those that are finished with either a result or an exception, and a set of tasks that are still running. One can control the behaviour of gather using `return_when` argument:

- `ALL_COMPLETED`: similar behaviour as `asynio.gather`
- `FIRST_EXCEPTION`: It's good when we’d like to cancel when one coroutine fails immediately with an exception. If they don't throw an exception, we must wait until they all end.
- `FIRST_COMPLETED`: similar behaviour as `asyncio.as_completed`. This can either be a coroutine that fails or one that runs successfully.

```python
# let's modify our fetch_status coroutine to accept a delay
import asyncio
from code.utils import delay, async_timed


async def fetch_status(session: aiohttp.ClientSession, url: str, delay_period: int = 0) -> int:
    await delay(delay_period)
    async with session.get(url) as resp:
        return resp.status


async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = [
            asyncio.create_task(fetch_status(session, "https://www.example.com", 1)),
            asyncio.create_task(fetch_status(session, "https://www.example.com", 4)),
            asyncio.create_task(fetch_status(session, "https://www.example.com", 4)),
        ]
        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            print(len(done), len(pending))


asyncio.run(main())
```

Unlike the `asyncio.gather` the exception are not thrown at the wait method, but we only get them when we await on the result from done set. which means we can control them better, since each task offer these two methods: `task.exception()` and `task.result()`

```python
import asyncio
import logging


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        good_request = fetch_status(session, 'https://www.example.com')
        bad_request = fetch_status(session, 'python://bad')
        fetchers = [
            asyncio.create_task(good_request),
            asyncio.create_task(bad_request),
        ]
        
        done, pending = await asyncio.wait(fetchers)
        print(f'Done task count: {len(done)}')
        print(f'Pending task count: {len(pending)}')
        
        for done_task in done:
            # result = await done_task will throw an exception
            if done_task.exception() is None:
                print(done_task.result())
            else:
                logging.error("Request got an exception",
                exc_info=done_task.exception())
asyncio.run(main())
```

```python
import asyncio
from code.utils import delay, async_timed

async def fetch_status(session: aiohttp.ClientSession, url: str, delay_period: int = 0) -> int:
    await delay(delay_period)
    async with session.get(url) as resp:
        return resp.status


async def main():
    async with aiohttp.ClientSession() as session:
        pending = [
            asyncio.create_task(fetch_status(session, "https://www.example.com", 1)),
            asyncio.create_task(fetch_status(session, "https://www.example.com", 4)),
            asyncio.create_task(fetch_status(session, "https://www.example.com", 4)),
        ]
        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            print(len(done), len(pending))


asyncio.run(main())
```

```python
import asyncio
import aiohttp


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        url = "https://www.example.com"
        pending = [
            asyncio.create_task(fetch_status(session, url)),
            asyncio.create_task(fetch_status(session, url)),
            asyncio.create_task(fetch_status(session, url)),
        ]
        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            print(f"Done task count: {len(done)}")
            print(f"Pending task count: {len(pending)}")
            for done_task in done:
                print(await done_task)


asyncio.run(main())
```

