# Web applications

## REST API using `aiohttp`

```python

from aiohttp import web
from aiohttp.web import Application
from datetime import datetime
from aiohttp.web_request import Request
from aiohttp.web_response import Response

routes = web.RouteTableDef()


@routes.get("/time")
async def time(request: Request) -> Response:
    today = datetime.today()
    return web.json_response(
        {"month": today.month, "day": today.day, "time": str(today.time())}
    )


app = web.Application()
app.add_routes(routes)
web.run_app(app)
```

`curl -i localhost:8080/time`

```python
from aiohttp import web
from aiohttp.web import Application
import asyncpg
from asyncpg import Pool
from aiohttp.web_request import Request
from aiohttp.web_response import Response

routes = web.RouteTableDef()
DB_KEY = "database"


async def create_database_pool(app: Application):
    print("Creating database pool.")
    pool: Pool = await asyncpg.create_pool(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        password="password",
        database="products",
        min_size=6,
        max_size=6,
    )
    app[DB_KEY] = pool


async def destroy_database_pool(app: Application):
    print("Destroying database pool.")
    pool: Pool = app[DB_KEY]
    await pool.close()


@routes.get("/brands")
async def get_brands(request: Request) -> Response:
    brand_query = "SELECT brand_id, brand_name FROM brand"
    pool = request.app[DB_KEY]
    async with pool.acquire() as conn:
        rows = await conn.fetch(brand_query)

    results = [dict(brand) for brand in rows]
    return web.json_response(results)


@routes.get("/products/{id}")
async def get_product(request: Request) -> Response:
    try:
        str_id = request.match_info["id"]  # A
        product_id = int(str_id)

        query = """
            SELECT
            product_id,
            product_name,
            brand_id
            FROM product
            WHERE product_id = $1
            """

        connection: Pool = request.app[DB_KEY]
        result = await connection.fetchrow(query, product_id)  # B

        if result:
            return web.json_response(dict(result))
        else:
            raise web.HTTPNotFound()
    except ValueError:
        raise web.HTTPBadRequest()


app = web.Application()
app.add_routes(routes)
app.on_startup.append(create_database_pool)
app.on_cleanup.append(destroy_database_pool)
web.run_app(app)

```



### Compare aiohttp and Flask

```python
# aiohttp server
from aiohttp import web
from aiohttp.web import Application
import asyncpg
from asyncpg import Pool
from aiohttp.web_request import Request
from aiohttp.web_response import Response

routes = web.RouteTableDef()
DB_KEY = "database"


async def create_database_pool(app: Application):
    print("Creating database pool.")
    pool: Pool = await asyncpg.create_pool(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        password="password",
        database="products",
        min_size=6,
        max_size=6,
    )
    app[DB_KEY] = pool


async def destroy_database_pool(app: Application):
    print("Destroying database pool.")
    pool: Pool = app[DB_KEY]
    await pool.close()


@routes.get("/brands")
async def get_brands(request: Request) -> Response:
    brand_query = "SELECT brand_id, brand_name FROM brand"
    pool = request.app[DB_KEY]
    async with pool.acquire() as conn:
        rows = await conn.fetch(brand_query)

    results = [dict(brand) for brand in rows]
    return web.json_response(results)


app = web.Application()
app.add_routes(routes)
app.on_startup.append(create_database_pool)
app.on_cleanup.append(destroy_database_pool)
web.run_app(app)
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

```
gunicorn -w 8 flasky:app 
wrk -t1 -c200 -d30s http://localhost:8000/brands

python3 main.py
wrk -t1 -c200 -d30s http://localhost:8000/brands
```



## `ASGI`

WSGI is a standardized way to forward web requests to a web framework, such as Flask or Django. WSGI operates based on request/response, meaning it won't support long-lived connection protocols, such as web-sockets.Gunicorn is a WSGI server. ASGI is the new cool-kid in the town, but is not standardised yet. ASGI fixes this by redesigning the API to use coroutines.

```python
#wsgi.py
def application(env, start_response):
    start_response("200 OK", [("Content-Type", "text/html")])
    return [b"WSGI hello!"]

```

`gunicorn wsgi:application`

` curl -i localhost:8000`

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

how do we serve the above application? There are a few implementation, one of the famous one is `uvicorn`

`uvicorn asgi:application`

https://mleue.com/

## Starlette or Fast API

### Simple program



### Websocket example

```python
import asyncio
from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute
from asgiref.sync import sync_to_async, async_to_sync

class UserCounter(WebSocketEndpoint):
    encoding = "text"
    sockets = []

    async def on_connect(self, websocket):
        await websocket.accept()
        self.sockets.append(websocket)
        await self._send_count()

    async def on_disconnect(self, websocket, close_code):
        self.sockets.remove(websocket)
        await self._send_count()

    async def on_receive(self, websocket, data):
        pass

    async def _send_count(self):
        if self.sockets:
            count_str = str(len(self.sockets))
            task_to_socket = {
                asyncio.create_task(websocket.send_text(count_str)): websocket
                for websocket in self.sockets
            }

            done, _ = await asyncio.wait(task_to_socket)

            for task in done:
                if task.exception() is not None:
                    if task_to_socket[task] in self.sockets:
                        self.sockets.remove(task_to_socket[task])


app = Starlette(routes=[WebSocketRoute("/counter", UserCounter)])

```

let's convert them to Fast API for fun?

## Django Asynchronous Views

https://fly.io/django-beats/running-tasks-concurrently-in-django-asynchronous-views/

`wrk -t1 -c200 -d30s http://localhost:8080/brands`