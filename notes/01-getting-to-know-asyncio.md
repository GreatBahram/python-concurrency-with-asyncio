# Konnichiwa :wave:, Concurrency

In today's world of web applications, there are so many I/O operations, such as:

- Downloading the content of a web page
- Communicating over a network
- Running several queries against a database.
- etc.

Most of these I/O operations tend to be slow for different reasons. Making man of these I/O requests at once can lead to substantial performance issues.

asyncio was first introduced in python 3.4 to handle these highly concurrent workloads outside of mulithreading and multiprocessing.

What will be covered:

- what is asyncio
- difference between CPU-bound vs I/O-bound
- Concurrency, parallelism, and multitasking
- Global Interpreter Lock
- non-blocking I/O + event loop

## What is asyncio?

In a synchronous application, code runs sequentially. 

One solution to this issue is to introduce **concurrency**, it means allowing more than on task being handled at the same time.

This lets us handle multiple I/O operations at once, while still allowing our application to remain responsive.

Instead of blocking all other application code waiting for that long-running task to be completed, the system is free to do other work that is not dependent on that task.

`asyncio` is a library to define coroutines and to execute these coroutines in an asynchronous fashion using a concurrency model known as a **single-threaded event loop**.

The next line of code runs as soon as the previous one has finished, and only one thing is happening at once. This model works fine for many, if not most, applications. However, what if one line of code is especially slow? In that case, all other code after our slow line will be stuck waiting for that line to complete.

In a synchronous application, we’ll be stuck waiting for those operations to complete before we can run anything else.

> [!TIP]
>
> One solution to this issue is to introduce **concurrency**, it means allowing more than on task being handled at the same time.

This lets us handle multiple I/O operations at once, while still allowing our application to remain responsive.

So what is asynchronous programming? It means that a particular long-running task can be run in the background separate from the main application. Instead of blocking all other application code waiting for that long-running task to be completed, the system is free to do other work that is not dependent on that task.

`asyncio` is a library to define coroutines and to execute these coroutines in an asynchronous fashion using a concurrency model known as a **single-threaded event loop**.

## CPU-bound vs I/O-bound

## Concurrency, parallelism, and multitasking

### Concurrency

When we say two tasks are happening concurrently, we mean those tasks are happening at the same time.

![image-20240830221930469](/home/bahram/projects/python-concurrency-with-asyncio/notes/01-getting-to-know-asyncio.assets/image-20240830221930469.png)

### Parallelism

When we say something is running in parallel, we mean not only are there two or more tasks happening concurrently, but they are also executing at the same time.

![image-20240830222019744](/home/bahram/projects/python-concurrency-with-asyncio/notes/01-getting-to-know-asyncio.assets/image-20240830222019744.png)

> [!NOTE]
>
> In a system that is only **concurrent**, we can <u>switch</u> between running these applications, running one application for a short while before letting the other one run.

### Multitasking

Multitasking itself is trivial, but there are generally two kinds of multitasking:

#### PREEMPTIVE MULTITASKING

In this model, we let the operating system decide how to switch between which work is currently being executed via a process called time slicing. Since the operating system switches between work, we call it **preempting**.

#### COOPERATIVE MULTITASKING

In this model,  we explicitly code points in our application where we can let other tasks run.

> [!NOTE]
>
> Here we are explicitly saying, “I’m pausing my task for a while; go ahead and run other tasks.”

The benefits of Cooperative multitasking:

- less resource intensive: As there is no context switch.
- More granularity: When operating system switches it may not be the best time to pause.

### Global Interpreter Lock (GIL)

GIL prevents one Python process from executing more than one Python bytecode instruction at any given time. This means that even if we have multiple threads on a machine with multiple cores, a Python process can have only one thread running Python code at a time.

> [!NOTE]
>
> Multiprocessing can run multiple bytecode instructions concurrently because each Python process has its own GIL.

So why does the GIL exist? The answer lies in how memory is managed in CPython.

The conflict with threads arises in that the implementation in CPython is not thread safe. When we say CPython is not thread safe, we mean that if two or more threads modify a shared variable, that variable may end in an unexpected state.

In other words, if you have a CPU-bound task, multithreading is not going to be beneficial for you.

Is the GIL ever released?

 The global interpreter lock is released when I/O operations happen

So how is it that we can release the GIL for I/O but not for CPU-bound operations?

The answer lies in **the system calls** that are made in the background. In the case of I/O, the low-level system calls are outside of the Python runtime.

#### asyncio and GIL

When we utilize `asyncio` we create objects called `coroutines`.
A `coroutine` can be thought of as executing a lightweight thread.

> [!IMPORTANT]
>
> Please note that asyncio does not circumvent the GIL, and we are still subject to it.

### non-blocking I/O + event loop

Let's use an example to better understand this.

Imagine we have a pair of sockets for communcation. Sockets are blocking by default.

Simply put, this means that when we are waiting for a server to reply with data, we halt our application or block it until we get data to read.
Thus, our application stops running any other tasks until we get data from the server, an error happens, or there is a timeout.

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the server's address and port
server_address = ('localhost', 8080)
sock.connect(server_address)

# Blocking read from the socket
data = sock.recv(1024)  # Blocking call
print(f"Received: {data.decode()}")
```

But at the  OS level we can operate in non-blocking mode, using something that is called event notification systems. Famous event notification systems:

- kqueue—FreeBSD and MacOS
- epoll—Linux
- IOCP (I/O completion port)—Windows



But how do we keep track of which tasks are waiting for I/O as opposed to ones that can just run because they are regular Python code? The answer lies in a construct called **an event loop.**

![img](/home/bahram/projects/python-concurrency-with-asyncio/slides/reveal.js/assets/event-loop.png)

The most basic event loop is extremely simple. We create a queue that holds a list
of events or messages.

```python
from collections import deque
messages = deque()

while True:
    if messages:
        message = messages.pop()
        process_message(message)

def make_request():
    cpu_bound_setup()
    io_bound_web_request()
    cpu_bound_postprocess()

task_one = make_request()
task_two = make_request()
task_three = make_request()
```

![image-20240830223601377](/home/bahram/projects/python-concurrency-with-asyncio/slides/reveal.js/assets/event-loop-output.png)