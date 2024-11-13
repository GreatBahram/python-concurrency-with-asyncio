import asyncio
from code.utils import delay, async_timed


@async_timed()
async def main():
    task = asyncio.create_task(delay(1))
    await task


asyncio.run(main())
