# Multi-threading

```python
from threading import Thread
import socket


def echo(client: socket.socket):
    while True:
        data = client.recv(2048)
        print(f"Received {data}, sending!")
        client.sendall(data)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 8000))
        server.listen()
        while True:
            connection, _ = server.accept()  # A
            thread = Thread(target=echo, args=(connection,))  # B
            thread.start()  # C


if __name__ == "__main__":
    main()

```

```python

def echo(client: socket.socket):
    while True:
        data = client.recv(2048)
        client.sendall(data)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 8000))
        server.listen()
        while True:
            threads = threading.enumerate()
            print(threads)

            conn, _ = server.accept()  # A
            print(f"Got a connection: {conn}")
            thread = Thread(target=echo, args=(conn,))  # B
            thread.start()  # C


if __name__ == "__main__":
    main()
```



```python
from threading import Thread
import socket
import threading


class ClientEchoThread(Thread):
    def __init__(self, client: socket.socket):
        super().__init__()
        self.client = client

    def run(self):
        try:
            while True:
                data = self.client.recv(2048)
                if not data:  # A
                    raise BrokenPipeError("Connection closed!")
                print(f"Received {data}, sending!")
                self.client.sendall(data)
        except OSError as e:  # B
            print(f"Thread interrupted by {e} exception, shutting down!")

    def close(self):
        if self.is_alive():  # C
            self.client.sendall(bytes("Shutting down!", encoding="utf-8"))
            self.client.shutdown(socket.SHUT_RDWR)  # D


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 8000))
        server.listen()
        threads: list[ClientEchoThread] = []

        try:
            while True:
                conn, _ = server.accept()  # A
                print(f"Got a connection: {conn}")
                thread = ClientEchoThread(conn)
                thread.start()
                threads.append(thread)
        except KeyboardInterrupt:
            print('Shutting down...')
            for thread in threads:
                thread.close()


if __name__ == "__main__":
    main()

```



```python
import requests
from concurrent.futures import ThreadPoolExecutor

from code.utils import sync_timed


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


@sync_timed()
def simple_sync():
    urls = ["https://www.example.com" for _ in range(100)]
    for url in urls:
        get_status_code(url)


@sync_timed()
def main():
    with ThreadPoolExecutor() as executor:
        urls = ["https://www.example.com" for _ in range(100)]
        results = executor.map(get_status_code, urls)
        for r in results:
            print(r)


main()

```

```python
import functools
from threading import Lock
import time
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

from code.utils import async_timed

counter_lock = Lock()
counter: int


async def reporter(total: int) -> None:
    while counter < total:
        print(f"Finished {counter}/{total} operations.")
        await asyncio.sleep(1)


def get_status_code(url: str) -> int:
    global counter
    import time

    time.sleep(0.4)
    with counter_lock:
        counter += 1
    return 200
    response = requests.get(url)
    return response.status_code


@async_timed()
async def main():
    global counter
    counter = 0

    request_count = 200
    url = "https://ipinfo.io"

    with ThreadPoolExecutor() as pool:
        loop = asyncio.get_running_loop()
        reporter_task = asyncio.create_task(reporter(request_count))
        urls = [url for _ in range(request_count)]
        tasks = [
            loop.run_in_executor(pool, functools.partial(get_status_code, url))
            for url in urls
        ]
        results = await asyncio.gather(*tasks)
        print(results)
        await reporter_task


asyncio.run(main())

```

```python
from threading import Lock, RLock, Thread
from typing import List

list_lock = RLock()


def sum_list(int_list: List[int]) -> int:
    print("Waiting to acquire lock...")
    with list_lock:
        print("Acquired lock.")
        if not int_list:
            print("Finished summing.")
            return 0
        else:
            head, *tail = int_list
            print("Summing rest of list.")
            return head + sum_list(tail)


thread = Thread(target=sum_list, args=([1, 2, 3, 4],))
thread.start()
thread.join()

```

```python
from threading import Lock, Thread
import time

lock_a = Lock()
lock_b = Lock()


def a():
    with lock_a:
        print("Acquired lock_a from method a!")
        time.sleep(1)
        with lock_b:
            print("Acquired both locks from method a!")


def b():
    with lock_b:
        print("Acquired lock b from method b!")
        with lock_a:
            print("Acquired both locks from method b!")


thread_1 = Thread(target=a)
thread_2 = Thread(target=b)
thread_1.start()
thread_2.start()
thread_1.join()
thread_2.join()

```

```python
import tkinter
from tkinter import ttk

window = tkinter.Tk()
window.title("Hello world app")
window.geometry("200x100")


def say_hello():
    print("Hello there!")


hello_button = ttk.Button(window, text="Say hello", command=say_hello)
hello_button.pack()

window.mainloop()

```

```python
import asyncio
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from queue import Queue
from threading import Thread
from tkinter import Entry, Label, Tk, ttk
from typing import Callable

from aiohttp import ClientSession


class StressTest:
    def __init__(
        self,
        loop: AbstractEventLoop,
        url: str,
        total_requests: int,
        callback: Callable[[int, int], None],
    ):
        self._completed_requests: int = 0
        self._load_test_future: Future | None = None
        self._loop = loop
        self._url = url
        self._total_requests = total_requests
        self._callback = callback
        self._refresh_rate = total_requests // 100

    def start(self) -> None:
        future = asyncio.run_coroutine_threadsafe(self._make_requests(), self._loop)
        self._load_test_future = future

    def cancel(self):
        if self._load_test_future:
            self._loop.call_soon_threadsafe(self._load_test_future.cancel)  # B

    async def _make_requests(self):
        async with ClientSession() as session:
            reqs = [
                self._get_url(session, self._url) for _ in range(self._total_requests)
            ]
            await asyncio.gather(*reqs)

    async def _get_url(self, session: ClientSession, url: str):
        try:
            return await session.get(url)
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            self._completed_requests = self._completed_requests + 1  # C
            if (
                self._completed_requests % self._refresh_rate == 0
                or self._completed_requests == self._total_requests
            ):
                self._callback(self._completed_requests, self._total_requests)


class LoadTester(Tk):
    def __init__(self, loop, *args, **kwargs):  # A
        Tk.__init__(self, *args, **kwargs)
        self._queue = Queue()
        self._refresh_ms = 25

        self._loop = loop
        self._load_test: StressTest | None = None
        self.title("URL Requester")

        self._url_label = Label(self, text="URL:")
        self._url_label.grid(column=0, row=0)

        self._url_field = Entry(self, width=10)
        self._url_field.grid(column=1, row=0)

        self._request_label = Label(self, text="Number of requests:")
        self._request_label.grid(column=0, row=1)

        self._request_field = Entry(self, width=10)
        self._request_field.grid(column=1, row=1)

        self._submit = ttk.Button(self, text="Submit", command=self._start)  # B
        self._submit.grid(column=2, row=1)

        self._pb_label = Label(self, text="Progress:")
        self._pb_label.grid(column=0, row=3)

        self._pb = ttk.Progressbar(
            self, orient="horizontal", length=200, mode="determinate"
        )
        self._pb.grid(column=1, row=3, columnspan=2)

    def _update_bar(self, pct: int):  # C
        if pct == 100:
            self._load_test = None
            self._submit["text"] = "Submit"
        else:
            self._pb["value"] = pct
            self.after(self._refresh_ms, self._poll_queue)

    def _queue_update(self, completed_requests: int, total_requests: int):  # D
        self._queue.put(int(completed_requests / total_requests * 100))

    def _poll_queue(self):
        if not self._queue.empty():
            percent_complete = self._queue.get()
            self._update_bar(percent_complete)
        else:
            if self._load_test:
                self.after(self._refresh_ms, self._poll_queue)

    def _start(self):  # F
        if self._load_test is None:
            self._submit["text"] = "Cancel"
            test = StressTest(
                self._loop,
                self._url_field.get(),
                int(self._request_field.get()),
                self._queue_update,
            )
            self.after(self._refresh_ms, self._poll_queue)
            test.start()
            self._load_test = test
        else:
            self._load_test.cancel()
            self._load_test = None
            self._submit["text"] = "Submit"


class ThreadedEventLoop(Thread):  # A
    def __init__(self, loop: AbstractEventLoop):
        super().__init__()
        self._loop = loop
        self.daemon = True

    def run(self):
        self._loop.run_forever()


loop = asyncio.new_event_loop()

asyncio_thread = ThreadedEventLoop(loop)
asyncio_thread.start()  # B

app = LoadTester(loop)  # C
app.mainloop()

```

