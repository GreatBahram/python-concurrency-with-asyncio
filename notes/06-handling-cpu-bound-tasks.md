# Handling CPU-bound work

Until now, we’ve been focused on performance gains we can get with `asyncio` when
running I/O-bound work concurrently. This seems like it severely limits asyncio, but the library is more versatile than just handling I/O-bound work.

`multiprocessing` library in python, letting us sidestep the global interpreter lock and take full advantage of a multi core machine. hence, using multithreading won’t provide any performance benefits.

Multiprocessing allows us instead of spawning threads to parallelize things, spawning subprocesses to handle our work. Each subprocess will have its own Python
interpreter and be subject to the GIL.

> [!NOTE]
> Even if we have more processes than cores, our operating system will use preemptive multitasking to allow our multiple tasks to run concurrently. This setup is both concurrent and parallel.



```python
from multiprocessing import Process
from code.utils import sync_timed


@sync_timed()
def count(until: int) -> int:
    counter = 0
    while counter < until:
        counter += 1
    return counter


@sync_timed()
def main():
    to_one_hundred_million = Process(target=count, args=(100_000_000,))
    to_two_hundred_million = Process(target=count, args=(200_000_000,))

    to_one_hundred_million.start()
    to_two_hundred_million.start()

    to_one_hundred_million.join()
    to_two_hundred_million.join()


if __name__ == "__main__":
    main()

```

This gives us a time savings over running sequentially, however there are two issues here:

- We don't have access to the results, unless we use shared inter-process memory!
- We also don't know which process completed first, something similar to `as_completed`
- We also need to instantiate our processes manually, which is not fun, right?

## Using process pools

With the help of process pool, we don't need to create process and start them:

```python
from multiprocessing import Pool
from code.utils import sync_timed


def greeting(name: str) -> str:
    return f"Salam, {name}"


@sync_timed()
def main():
    with Pool() as process_pool:
        salam_bahram = process_pool.apply(greeting, args=("Bahram",))
        salam_mitra = process_pool.apply(greeting, args=("Mitra",))
        salam_saeid = process_pool.apply(greeting, args=("Saeid",))
        print(salam_bahram, salam_mitra, salam_saeid)


if __name__ == "__main__":
    main()

```

> [!note]
> This works, but there is an issue here. It runs each process **sequentially**, negating the point of running in parallel.

```python
from multiprocessing import Pool
from code.utils import sync_timed


@sync_timed()
def greeting(name: str) -> str:
    return f"Salam, {name}"


@sync_timed()
def main():
    with Pool() as process_pool:
        # salam_bahram = process_pool.apply(greeting, args=("Bahram",))
        # salam_mitra = process_pool.apply(greeting, args=("Mitra",))
        # salam_saeid = process_pool.apply(greeting, args=("Saeid",))
        # print(salam_bahram, salam_mitra, salam_saeid)
        salam_bahram = process_pool.apply_async(greeting, args=("Bahram",))
        salam_mitra = process_pool.apply_async(greeting, args=("Mitra",))
        salam_saeid = process_pool.apply_async(greeting, args=("Saeid",))
        results = salam_bahram.get(), salam_saeid.get(), salam_mitra.get()
        print(results)


if __name__ == "__main__":
    main()

```

>  [!NOTE]
> `apply_async` lets things run concurrently, but what if one of them takes more time than the other one? The second issue that was about having something similar to `as_completed` is still there!



## Best of Both Worlds

Most of the time, multiprocessing is good for simple use cases. Python offers a very good abstraction in `concurrent.futures`. This module contains executors for both processes and threads that can be used on their own but also interoperate with asyncio.



Here, let's take a look at the Executer abstraction from `concurrent.futures`. It offers two methods for running tasks asynchronously:

- `submit`: which will take a `callable` and return a `Future`
- `map`: This method will take a callable and a list of function arguments and then execute each argument in the list asynchronously. It returns an iterator of the results of our calls ==similarly== to `asyncio.as_completed` in that results are available once they complete. However, we aren’t quite as responsive as `asyncio.as_completed`.

Let's give it a try:

```python
from code.utils import sync_timed
from concurrent.futures import ProcessPoolExecutor


@sync_timed()
def count(until: int) -> int:
    counter = 0
    while counter < until:
        counter += 1
    return counter


@sync_timed()
def main():
    with ProcessPoolExecutor() as executer:
        # NOTE: put the 100 M at first position and then run it as well.
        nums = [1, 1, 2, 3, 5, 8, 100_000_000]

        for r in executer.map(count, nums):
            print(r)


if __name__ == "__main__":
    main()

```

### Use Executor with asyncio

What is really cool is that we can easily hook them into the asyncio event loop. There is a special method on the event loop called `run_in_executor` that takes an executor as well as a callable and it will run that callable inside the pool. Then it returns an awaitable, which we can use it with the methods such as `gather`, `as_completed` and `wait`.

> [!note]
>
> Please note, `run_in_executor` only takes a callable and does not allow us to supply function arguments; so we need to use `functools.partial` to feed these arguments.

```python
import asyncio
from functools import partial
from code.utils import async_timed, sync_timed
from concurrent.futures import ProcessPoolExecutor


@sync_timed()
def count(until: int) -> int:
    counter = 0
    while counter < until:
        counter += 1
    return counter


@async_timed()
async def main():
    with ProcessPoolExecutor() as executer:
        loop = asyncio.get_running_loop()
        nums = [1, 1, 2, 3, 5, 8, 100_000_000]
        calls = [partial(count, num) for num in nums]

        fs: list[asyncio.Future] = []

        for call in calls:
            fs.append(loop.run_in_executor(executer, call))

        for item in asyncio.as_completed(fs):
            result = await item
            print(result)


if __name__ == "__main__":
    asyncio.run(main())

```

## MapReduce

In order to benefit from our resources, sometimes we need to use MapReduce approach, which consists of two main stages:

- Map: The input data is first split into smaller blocks.
- Reduce:  Once the problem for each subset is solved, we can then combine the results into
  a final answer. It is called reducing as we “reduce” multiple answers into one.

Counting the frequency of words in a large text data set is a canonical Map-Reduce problem.

Let's take a look at a simple example:

```python
from collections import Counter
from functools import reduce
import textwrap


TEXT = textwrap.dedent("""\
دنیا همه هیچ و اهل دنیا همه هیچ
ای هیچ برای هیچ بر هیچ مپیچ
دانی که پس از عمر چه ماند باقی
مهر است و محبت است و باقی همه هیچ""")


def map_frequency(text: str) -> Counter[str]:
    return Counter(text.split())


def merge(first: Counter[str], second: Counter[str]) -> Counter[str]:
    return first + second


def main():
    intermediate_results = [map_frequency(line) for line in TEXT.splitlines()]
    final_result = reduce(merge, intermediate_results)
    print(final_result)


if __name__ == "__main__":
    main()

```

For the real test though, we are using a relatively large dataset, which is called [Goolge Books Ngrams](https://books.google.com/ngrams/info) that is a scan of n-grams from a set of over 8,000,000 books, going back to the year 1500, comprising more than six percent of all books published. You can download the dataset [here](https://mattfowler.io/data/googlebooks-eng-all-1gram-20120701-a.gz).

Let's take a look at it:

```shell
❯ head google_books_ngram.txt 
A'Aang_NOUN     1879    45      5
A'Aang_NOUN     1882    5       4
A'Aang_NOUN     1885    1       1
A'Aang_NOUN     1891    1       1
A'Aang_NOUN     1899    20      4
A'Aang_NOUN     1927    3       1
A'Aang_NOUN     1959    5       2
A'Aang_NOUN     1962    2       2
A'Aang_NOUN     1963    1       1
A'Aang_NOUN     1966    45      13
```

- What this means is that the word `A'Aang_NOUN` appeared 45 times in 1879, and in 5 books.

first we do it synchronously and the we are try to expedite it using Executor + asyncio.

```python
from collections import Counter
from functools import reduce
import textwrap

from code.utils import sync_timed


@sync_timed()
def simple_sync():
    with open("code/google_books_ngrams.txt", mode="rt") as fp:
        content = fp.readlines()

    freq = Counter()
    for line in content:
        parts = line.split("\t")
        word = parts[0]
        count = int(parts[2])

        freq[word] += count


@sync_timed()
def main():
    simple_sync()


if __name__ == "__main__":
    main()

```

```shell
❯ python3 main.py
Starting <function main at 0x7f5fd276c720> with args () {}
Starting <function simple_sync at 0x7f5fd3388220> with args () {}
finsihed <function simple_sync at 0x7f5fd3388220> in 55.2526 second(s)
finsihed <function main at 0x7f5fd276c720> in 55.2526 second(s)
```

It took around 55 seconds for the synchronous approach.

Now, let's make it more efficient using map-reduce approach. Firstly, we need to split the data between the processes, however probably not passing a single line to a process, this is because when you pass data to a process you need to serialize it and if it is too small you're not gonna see any benefit.

```python
import asyncio
from collections import Counter
from collections.abc import Iterable
from functools import partial, reduce
from itertools import batched
from typing import Final
from concurrent.futures import ProcessPoolExecutor

from code.utils import async_timed

CHUNK_SIZE: Final[int] = 60_000


def map_frequency(lines: Iterable[str]) -> dict[str, int]:
    counter = Counter()
    for line in lines:
        parts = line.split("\t")
        word = parts[0]
        count = int(parts[2])
        counter[word] += count
    return counter


def merge_dictionaries(first: dict[str, int], second: dict[str, int]) -> dict[str, int]:
    merged = first
    for key in second:
        merged[key] = merged.get(key, 0) + second[key]
    return merged


@async_timed()
async def main():
    with open("code/google_books_ngrams.txt", mode="rt") as fp:
        content = fp.readlines()

    loop = asyncio.get_running_loop()
    fs: list[asyncio.Task] = []

    with ProcessPoolExecutor() as executor:
        for chunk in batched(content, CHUNK_SIZE):
            fs.append(loop.run_in_executor(executor, partial(map_frequency, chunk)))

        intermediate_results = await asyncio.gather(*fs)

    final_result = reduce(merge_dictionaries, intermediate_results)
    print(final_result["Aardvark"])


if __name__ == "__main__":
    asyncio.run(main())

```



This truly improved the performance of the synchronous app that we had, however right now there isn’t an easy way to see how many map operations we’ve completed at any given time. In a sync application, it's easy to add a counter what should we do in multi-processing application?

## Shared data

Multiprocessing supports a concept called shared memory objects. MP supports two types of shared data:

- Value
- Array: can only holds [these values](https://docs.python.org/3/library/array.html#module-array)

```python
from multiprocessing import Process, Value, Array
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray


def increment_value(shared_int: Synchronized[int]):
    shared_int.value += 1


def increment_array(shared_array: SynchronizedArray[int]):
    for idx, integer in enumerate(shared_array):
        shared_array[idx] = integer + 1


if __name__ == "__main__":
    integer = Value("i", 0)
    integer_array = Array("i", [0, 0])

    procs = [
        Process(target=increment_value, args=(integer,)),
        Process(target=increment_array, args=(integer_array,)),
    ]

    for p in procs:
        p.start()
    for p in procs:
        p.join()

    print(integer.value)
    print(integer_array[:])

```

### Race condition

```python
from multiprocessing import Process, Value


def increment_value(shared_int: Value):
    shared_int.value = shared_int.value + 1


if __name__ == "__main__":
    for _ in range(100):
        integer = Value("i", 0)

        procs = [
            Process(target=increment_value, args=(integer,)),
            Process(target=increment_value, args=(integer,)),
        ]

        for p in procs:
            p.start()
        for p in procs:
            p.join()

        assert integer.value == 2

```

A race condition occurs when the outcome of a set of operations is dependent on which operation finishes first.

The problem lies in that incrementing a value involves both read and write operations. Incrementing is written as two operations, which causes this issue. This makes it non-atomic or not thread-safe.

In order to fix this, we need to introduce a `lock` also known as `mutex` (**mutual exclusion**). The lock section of the code is called **critical section**. Let's use a lock and resolve the race condition issue:

```python
from multiprocessing import Process, Value


def increment_value(shared_int: Value):
    with shared_int.get_lock():
        shared_int.value = shared_int.value + 1


if __name__ == "__main__":
    for _ in range(1_000):
        integer = Value("i", 0)

        procs = [
            Process(target=increment_value, args=(integer,)),
            Process(target=increment_value, args=(integer,)),
        ]

        for p in procs:
            p.start()
        for p in procs:
            p.join()

        assert integer.value == 2

```

Notice that we have taken concurrent code and have just forced it to be sequential, negating the value of running in parallel. This is an important observation!

Let's count the progress of `map_frequency` in our code using the shared data:

```python
import functools
import asyncio
import math
from multiprocessing import Value
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
from collections.abc import Iterable
from functools import partial
from itertools import batched
from typing import Final

from code.utils import async_timed

map_progress: Value

CHUNK_SIZE: Final[int] = 60_000


def init(counter: Value):
    global map_progress
    map_progress = counter


def increment():
    with map_progress.get_lock():
        map_progress.value += 1


def map_frequency(lines: Iterable[str]) -> dict[str, int]:
    counter = Counter()
    for line in lines:
        parts = line.split("\t")
        word = parts[0]
        count = int(parts[2])
        counter[word] += count

    with map_progress.get_lock():
        map_progress.value += 1

    return counter


def merge_dictionaries(first: dict[str, int], second: dict[str, int]) -> dict[str, int]:
    merged = first
    for key in second:
        merged[key] = merged.get(key, 0) + second[key]
    return merged


async def reporter(total: int) -> None:
    global map_progress
    while map_progress.value < total:
        print(f"Finished {map_progress.value}/{total} map operation")

        await asyncio.sleep(1)


@async_timed()
async def main():
    global map_progress

    with open("code/google_books_ngrams.txt", mode="rt") as fp:
        content = fp.readlines()

    loop = asyncio.get_running_loop()
    fs: list[asyncio.Task] = []
    total = math.ceil(len(content) // CHUNK_SIZE)
    map_progress = Value("i", 0)

    with ProcessPoolExecutor(initializer=init, initargs=(map_progress,)) as executor:
        reporter_task = asyncio.create_task(reporter(total))

        for chunk in batched(content, CHUNK_SIZE):
            fs.append(loop.run_in_executor(executor, partial(map_frequency, chunk)))

        intermediate_results = await asyncio.gather(*fs)
        await reporter_task

    final_result = functools.reduce(merge_dictionaries, intermediate_results)
    print(final_result["Aardvark"])


if __name__ == "__main__":
    asyncio.run(main())

```
