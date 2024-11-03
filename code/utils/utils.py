import asyncio


async def delay(seconds: int) -> None:
    print("Sleeping for {seconds} seconds.")
    await asyncio.sleep(seconds)
    print("Finished sleeping for {seconds} seconds.")
    return seconds
