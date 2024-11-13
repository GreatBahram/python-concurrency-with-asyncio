import asyncio
import logging
import signal
import socket
import selectors
from selectors import DefaultSelector


CRLF = b"\r\n"


# echo - server
def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    address = ("localhost", 8000)
    server_sock.setblocking(False)
    server_sock.bind(address)
    server_sock.listen()

    sel = DefaultSelector()
    sel.register(server_sock, selectors.EVENT_READ)

    while True:
        events = sel.select(timeout=1)

        if not events:
            continue

        for event, _ in events:
            event_sock = event.fileobj
            if event_sock == server_sock:
                conn, addr = server_sock.accept()
                conn.setblocking(False)
                sel.register(conn, selectors.EVENT_READ)
                print(f"Got a connection: {conn}")
            else:
                buffer = b""

                while buffer[-2:] != CRLF:
                    data = event_sock.recv(2)
                    if not data:
                        break
                    buffer += data
                    print(f"Got a data: {data}")

                print(f"Buffer: {buffer}")
                event_sock.sendall(buffer)


# main()


async def echo(sock: socket.socket, loop: asyncio.AbstractEventLoop) -> None:
    try:
        while data := await loop.sock_recv(sock, 1024):
            if data == b"boom\r\n":
                raise Exception("Error occurred.")
            print(f"Data: {data}")
            await loop.sock_sendall(sock, data)
    except Exception as ex:
        logging.exception(ex)
    finally:
        sock.close()


echo_tasks: list[asyncio.Task] = []


async def listen_for_connenction(
    server_sock: socket.socket, loop: asyncio.AbstractEventLoop
) -> None:
    while True:
        conn, addr = await loop.sock_accept(server_sock)
        conn.setblocking(False)
        print(f"Got a connection: {conn}")
        echo_tasks.append(asyncio.create_task(echo(conn, loop)))


async def close_echo_tasks(echo_tasks: list[asyncio.Task]) -> None:
    print("Got a SIGINT")
    waited_tasks = [asyncio.wait_for(t, 2) for t in echo_tasks]
    for t in waited_tasks:
        try:
            await t
        except asyncio.TimeoutError:
            pass


async def main() -> None:
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    address = ("localhost", 8000)
    server_sock.setblocking(False)
    server_sock.bind(address)
    server_sock.listen()

    loop.add_signal_handler(signal.SIGINT, shutdown)

    await listen_for_connenction(server_sock, loop)


class GracefulExit(SystemExit):
    pass


def shutdown():
    raise GracefulExit


loop = asyncio.new_event_loop()

try:
    loop.run_until_complete(main())
except GracefulExit:
    loop.run_until_complete(close_echo_tasks(echo_tasks))
finally:
    loop.close()
