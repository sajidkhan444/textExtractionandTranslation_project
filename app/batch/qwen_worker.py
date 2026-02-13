# app/batch/qwen_worker.py

from app.batch.queue_manager import qwen_queue, translation_queue
from app.services.normalization_qwen import normalize_batch
from app.services.keywords import extract_keywords_batch_hybrid


async def qwen_worker():

    while True:

        data = await qwen_queue.get()

        batch = data["batch"]
        cleaned_texts = data["cleaned"]
        timestamped = data["timestamped"]

        normalized = normalize_batch(cleaned_texts)
        keywords_batch = extract_keywords_batch_hybrid(normalized)

        await translation_queue.put({
            "batch": batch,
            "normalized": normalized,
            "timestamped": timestamped,
            "keywords": keywords_batch
        })
