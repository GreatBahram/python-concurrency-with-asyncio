# Asynchronous Web Applications

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
# FastAPI program
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Connection, Record
from asyncpg.pool import Pool
from typing import AsyncGenerator, List, Dict
from fastapi import Depends, FastAPI


db_pool: Pool


async def create_database_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        password="password",
        database="products",
        min_size=6,
        max_size=6,
    )


async def destroy_database_pool():
    global db_pool
    await db_pool.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_database_pool()
    yield
    await destroy_database_pool()


async def get_connection() -> AsyncGenerator[None, Connection]:
    async with db_pool.acquire() as conn:
        yield conn


app = FastAPI(lifespan=lifespan)


@app.get("/brands")
async def brands(conn: Connection = Depends(get_connection)):
    brand_query = "SELECT brand_id, brand_name FROM brand"
    results: List[Record] = await conn.fetch(brand_query)
    result_as_dict: List[Dict] = [dict(brand) for brand in results]
    return result_as_dict
```

```python
# flask app
from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)
conn_info = "dbname=products user=postgres password=password host=127.0.0.1"
db = psycopg2.connect(conn_info)


@app.route("/brands")
def brands():
    cur = db.cursor()
    cur.execute("SELECT brand_id, brand_name FROM brand")
    rows = cur.fetchall()
    cur.close()
    return jsonify([{"brand_id": row[0], "brand_name": row[1]} for row in rows])

```

```shell
# Test the async app
> uvicorn --workers 8 main:app --log-level error
> wrk -t1 -c200 -d30s http://localhost:8000/brands

# Test the flask application
> gunicorn -w 8 flasky:app
> wrk -t1 -c200 -d30s http://localhost:8000/brands
```

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

## Django Asynchronous Views

```shell
pip install django
django-admin startproject async_views
gunicorn async_views.asgi:application -k uvicorn.workers.UvicornWorker
python3 manage.py startapp async_api
```

https://fly.io/django-beats/running-tasks-concurrently-in-django-asynchronous-views/
