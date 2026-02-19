
# app/batch/qwen_worker.py

from app.batch.queue_manager import qwen_queue, translation_queue
from app.services.qwen import extract_keywords_batch
from app.core.logger import logger


async def qwen_worker():

    while True:

        data = await qwen_queue.get()

        batch = data["batch"]

        logger.info(f"🧠 Qwen batch received | size={len(batch)}")

        texts = [item["normalized"] for item in batch]

        for item in batch:
            logger.info(f"🧠 Keyword extraction started | videoId={item['video_id']}")

        keywords_batch = extract_keywords_batch(texts)

# Attach keywords directly into each item
        for item, kws in zip(batch, keywords_batch):
            item["keywords"] = kws
            logger.info(f"✅ Keyword extraction completed | videoId={item['video_id']}")

# Forward full batch
        await translation_queue.put({
            "batch": batch
        })
