# app/batch/batch_collector.py

from app.batch.queue_manager import input_queue, demucs_queue
from app.core.settings import MAX_BATCH_SIZE, BATCH_TIMEOUT
import asyncio


async def batch_collector_worker():

    while True:

        batch = []

        try:
            # Always wait for first item
            item = await input_queue.get()
            batch.append(item)

            # Try to fill batch
            while len(batch) < MAX_BATCH_SIZE:
                try:
                    item = await asyncio.wait_for(
                        input_queue.get(),
                        timeout=BATCH_TIMEOUT
                    )
                    batch.append(item)
                except asyncio.TimeoutError:
                    break

            # Send full batch to next stage
            await demucs_queue.put(batch)

        except Exception as e:
            print("Batch Collector Error:", e)
