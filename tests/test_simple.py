import asyncio
import sys

import pytest

from multi_queue import Broadcast

if sys.version_info < (3, 10):
    from asyncstdlib import anext

    def aiter(it):
        return it.__aiter__()


pytestmark = pytest.mark.asyncio

ENOUGH_TIME_TO_LAUNCH_ALL_TASKS = 0.01


async def test_lockstep():
    async def check_next_value(consumer, value):
        assert await anext(consumer) == value

    queue = Broadcast()
    nb_values = 10
    nb_consumers = 10
    consumers = [aiter(queue) for _ in range(nb_consumers)]
    for i in range(nb_values):
        queue.put(i)
        await asyncio.gather(
            *(asyncio.create_task(check_next_value(consumer, i)) for consumer in consumers)
        )


async def test_close():
    queue = Broadcast()
    nb_values = 10
    nb_consumers = 1

    async def consume():
        total = 0
        async for value in queue:
            print(value)
            total += value
        return total

    tasks = [asyncio.create_task(consume()) for _ in range(nb_consumers)]
    await asyncio.sleep(ENOUGH_TIME_TO_LAUNCH_ALL_TASKS)
    for i in range(nb_values):
        queue.put(i)
    # closing the queue before any consumer has processed any value
    queue.close()
    total_sum = sum(await asyncio.gather(*tasks))
    assert total_sum == ((nb_values - 1) * nb_values / 2) * nb_consumers
