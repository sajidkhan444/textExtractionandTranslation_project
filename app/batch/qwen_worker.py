# app/batch/qwen_worker.py

from app.batch.queue_manager import qwen_queue, translation_queue
from app.services.keywords import extract_keywords_batch_hybrid
from app.core.settings import QWEN_MICRO_BATCH_SIZE, QWEN_BUFFER_TIMEOUT
from app.core.logger import logger
import asyncio


# async def qwen_worker():

#     while True:

#         data = await qwen_queue.get()

#         batch = data["batch"]

#         logger.info(f"🧠 Qwen batch received | size={len(batch)}")

#         texts = [item["normalized"] for item in batch]

#         for item in batch:
#             logger.info(f"🧠 Keyword extraction started | videoId={item['video_id']}")

#         # FIXED FUNCTION NAME
#         keywords_batch = extract_keywords_batch_hybrid(texts)

#         for item, kws in zip(batch, keywords_batch):
#             item["keywords"] = kws
#             logger.info(f"✅ Keyword extraction completed | videoId={item['video_id']}")

#         await translation_queue.put({
#             "batch": batch
#         })

QWEN_MICRO_BATCH_SIZE = 4  # Collect 4 samples before processing
QWEN_BUFFER_TIMEOUT = 1.0  # Don't wait too long for samples


async def qwen_worker():

    buffer = []
    
    while True:

        try:
            # Try to get a sample with timeout
            sample = await asyncio.wait_for(
                qwen_queue.get(),
                timeout=QWEN_BUFFER_TIMEOUT
            )
            buffer.append(sample["sample"])

            # Process when buffer reaches micro-batch size
            if len(buffer) >= QWEN_MICRO_BATCH_SIZE:
                await _process_qwen_batch(buffer)
                buffer = []

        except asyncio.TimeoutError:
            # Process whatever is in buffer (if anything)
            if buffer:
                logger.info(f"🧠 Qwen timeout - processing partial batch | size={len(buffer)}")
                await _process_qwen_batch(buffer)
                buffer = []


async def _process_qwen_batch(batch):
    
    logger.info(f"🧠 Qwen batch received | size={len(batch)}")

    texts = [item["normalized"] for item in batch]

    for item in batch:
        logger.info(f"🧠 Keyword extraction started | videoId={item['video_id']}")

    # Extract keywords for the batch
    keywords_batch = extract_keywords_batch_hybrid(texts)

    # Send EACH sample individually to translation_queue immediately
    for item, kws in zip(batch, keywords_batch):
        item["keywords"] = kws
        logger.info(f"✅ Keyword extraction completed | videoId={item['video_id']}")
        
        # Send individually for next stage
        await translation_queue.put({"sample": item})