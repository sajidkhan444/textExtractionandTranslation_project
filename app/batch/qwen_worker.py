
# app/batch/qwen_worker.py
from app.batch.queue_manager import qwen_queue, translation_queue
from app.batch.queue_manager import qwen_queue, translation_queue
from app.services.qwen import extract_keywords_batch


async def qwen_worker():

    while True:

        data = await qwen_queue.get()

        batch = data["batch"]

        texts = [item["normalized"] for item in batch]

        keywords_batch = extract_keywords_batch(texts)

        # Attach keywords directly into each item
        for item, kws in zip(batch, keywords_batch):
            item["keywords"] = kws

        # Forward full batch
        await translation_queue.put({
            "batch": batch
        })
