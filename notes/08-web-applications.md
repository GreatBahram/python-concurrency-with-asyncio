# Asynchronous Web Applications
## `ASGI`

WSGI is a standardized way to forward web requests to a web framework, such as Flask or Django. WSGI operates based on request/response, meaning it won't support long-lived connection protocols, such as web-sockets. Gunicorn is a WSGI server.

```python
#wsgi.py
def application(env, start_response):
    start_response("200 OK", [("Content-Type", "text/html")])
    return [b"WSGI hello!"]

```

```shell
# ask gunicorn to run our custom wsgi app
gunicorn wsgi:application

# Test it out
curl -i localhost:8000
```

ASGI is the new cool-kid in the town, but is not standardised yet. ASGI fixes request/response issue by redesigning the API to use coroutines.

```python
# asgi.py
from typing import Coroutine


async def application(scope: dict, receive: Coroutine, send: Coroutine):
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/html"]],
        }
    )
    await send({"type": "http.response.body", "body": b"ASGI hello!"})

```

How do we serve the above application? There are a few implementation, one of the famous one is `uvicorn`

`uvicorn asgi:application`

https://mleue.com/

## REST API using FastAPI

```python
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()


@app.get("/time")
async def time():
    today = datetime.today()
    return {"month": today.month, "day": today.day, "time": str(today.time())}

```

```shell
# use this command to run the server
fastapi dev main.py

# use this to call the api
curl -i localhost:8080/time
```

### Comparing FastAPI and Flask

Make sure you've the database instance running

```shell
docker run -d --name my-postgres-container -p 5432:5432 my-postgres
```

```python
from fastapi import Depends, FastAPI
from asyncpg import Pool, Record
import asyncpg
from contextlib import asynccontextmanager


class DatabasePool:
    _pool: Pool = None

    @classmethod
    async def create_database_pool(
        cls,
    ):
        if cls._pool is None:
            print("Setting up database pool...")
            cls._pool = await asyncpg.create_pool(
                host="127.0.0.1",
                port=5432,
                user="postgres",
                database="products",
                password="password",
                min_size=6,
                max_size=6,
            )

    @classmethod
    async def destroy_database_pool(cls):
        if cls._pool:
            print("Destroying database pool...")
            await app.state.DB_POOL.close()

    @classmethod
    async def get_pool(cls) -> Pool:
        if cls._pool is None:
            raise ValueError("Vaaaaay, nah 😢")
        return cls._pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await DatabasePool.create_database_pool()
    yield
    await DatabasePool.destroy_database_pool()


app = FastAPI(lifespan=lifespan)


@app.get("/brands")
async def get_brands(pool: Pool = Depends(DatabasePool.get_pool)):
    async with pool.acquire() as conn:
        brand_query = "select brand_id, brand_name from brand"
        results: list[Record] = await conn.fetch(brand_query)
        return [dict(r) for r in results]

```



```shell
# Test the async app
> uvicorn --workers 8 main:app --log-level error
> wrk -t1 -c200 -d30s http://localhost:8000/brands
```

### Websocket with FastAPI

```python
import asyncio
from contextlib import suppress
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI()


class UserCounter:
    def __init__(self):
        self._sockets: list[WebSocket] = []

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sockets.append(websocket)
        await self._send_count()

    async def on_disconnect(self, websocket: WebSocket):
        self._sockets.remove(websocket)
        await self._send_count()

    async def on_receive(self, ws: WebSocket, data: bytes) -> None:
        pass

    async def _send_count(self):
        if self._sockets:
            count_str = str(len(self._sockets))
            task_to_socket = {
                asyncio.create_task(ws.send_text(count_str)): ws for ws in self._sockets
            }
            done, pending = await asyncio.wait(task_to_socket)
            for task_done in done:
                if task_done.exception() is not None:
                    with suppress(ValueError):
                        self._sockets.remove(task_to_socket[task_done])


user_counter = UserCounter()


@app.websocket("/counter")
async def connection_counter(websocket: WebSocket):
    await user_counter.on_connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await user_counter.on_receive(ws=websocket, data=data)
    except WebSocketDisconnect:
        await user_counter.on_disconnect(websocket)

```
