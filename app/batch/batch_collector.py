import asyncio
from app.core.settings import MAX_BATCH_SIZE, BATCH_TIMEOUT

async def collect_batch(queue):

    batch = []

    try:
        item = await queue.get()
        batch.append(item)

        while len(batch) < MAX_BATCH_SIZE:
            try:
                item = await asyncio.wait_for(
                    queue.get(),
                    timeout=BATCH_TIMEOUT
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break

    except Exception as e:
        print("Batch collection error:", e)

    return batch
