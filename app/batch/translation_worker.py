# app/batch/translation_worker.py

import os
import requests
from app.batch.queue_manager import translation_queue
from app.services.translation import translate_batch_multilang
from app.core.settings import TRANSLATION_MICRO_BATCH_SIZE, TRANSLATION_BUFFER_TIMEOUT
from app.core.logger import logger
import asyncio

AWS_WEBHOOK_URL = "https://api.hippitch.net/ai-services/webhooks/transcription"
WEBHOOK_SECRET = "3f9b7c8e2a4d6f1b9c0e7a2d4f8c1b6a"


# async def translation_worker():

#     while True:

#         data = await translation_queue.get()

#         batch = data["batch"]

#         logger.info(f"🌍 Translation batch received | size={len(batch)}")

#         texts = [item["normalized"] for item in batch]

#         for item in batch:
#             logger.info(f"🌍 Translation started | videoId={item['video_id']}")

#         translations = translate_batch_multilang(texts)

#         for item, trans in zip(batch, translations):

#             logger.info(f"📤 Preparing webhook payload | videoId={item['video_id']}")

#             payload = {
#                 "videoId": item["video_id"],
#                 "transcription": item["normalized"],
#                 "summary": item["normalized"][:500],
#                 "keywords": item["keywords"],
#                 "translations": {
#                     "es": trans["spanish_full"],
#                     "de": trans["german_full"]
#                 }
#             }
       


#             for attempt in range(3):
#                 try:
#                     logger.info(
#                         f"📡 Sending result to AWS | videoId={item['video_id']} | attempt={attempt+1}"
#                     )

#                     requests.post(
#                         AWS_WEBHOOK_URL,
#                         json=payload,
#                         headers={
#                             "Content-Type": "application/json",
#                             "x-webhook-secret": WEBHOOK_SECRET
#                         },
#                         timeout=30
#                     )

#                     logger.info(
#                         f"🚀 Job completed & handed over to AWS | videoId={item['video_id']}"
#                     )
#                     break

#                 except Exception as e:
#                     logger.error(
#                         f"⚠️ Webhook failed | videoId={item['video_id']} | error={str(e)}"
#                     )

#             if os.path.exists(item["temp_path"]):
#                 os.remove(item["temp_path"])
#                 logger.info(
#                     f"🧹 Temp file removed | videoId={item['video_id']}"
#                 )

TRANSLATION_MICRO_BATCH_SIZE = 4  # Collect 4 samples before processing
TRANSLATION_BUFFER_TIMEOUT = 1.0  # Don't wait too long for samples


async def translation_worker():

    buffer = []
    
    while True:

        try:
            # Try to get a sample with timeout
            sample = await asyncio.wait_for(
                translation_queue.get(),
                timeout=TRANSLATION_BUFFER_TIMEOUT
            )
            buffer.append(sample["sample"])

            # Process when buffer reaches micro-batch size
            if len(buffer) >= TRANSLATION_MICRO_BATCH_SIZE:
                await _process_translation_batch(buffer)
                buffer = []

        except asyncio.TimeoutError:
            # Process whatever is in buffer (if anything)
            if buffer:
                logger.info(f"🌍 Translation timeout - processing partial batch | size={len(buffer)}")
                await _process_translation_batch(buffer)
                buffer = []


async def _process_translation_batch(batch):
    
    logger.info(f"🌍 Translation batch received | size={len(batch)}")

    texts = [item["normalized"] for item in batch]

    for item in batch:
        logger.info(f"🌍 Translation started | videoId={item['video_id']}")

    # Translate the batch
    translations = translate_batch_multilang(texts)

    # Process each sample individually
    for item, trans in zip(batch, translations):

        logger.info(f"📤 Preparing webhook payload | videoId={item['video_id']}")

        payload = {
            "videoId": item["video_id"],
            "transcription": item["normalized"],
            "summary": item["normalized"][:500],
            "keywords": item["keywords"],
            "translations": {
                "es": trans["spanish_full"],
                "de": trans["german_full"]
            }
        }

        # Send webhook with retries
        for attempt in range(3):
            try:
                logger.info(
                    f"📡 Sending result to AWS | videoId={item['video_id']} | attempt={attempt+1}"
                )

                requests.post(
                    AWS_WEBHOOK_URL,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-webhook-secret": WEBHOOK_SECRET
                    },
                    timeout=30
                )

                logger.info(
                    f"🚀 Job completed & handed over to AWS | videoId={item['video_id']}"
                )
                break

            except Exception as e:
                logger.error(
                    f"⚠️ Webhook failed | videoId={item['video_id']} | error={str(e)}"
                )

        # Clean up temp file
        if os.path.exists(item["temp_path"]):
            os.remove(item["temp_path"])
            logger.info(
                f"🧹 Temp file removed | videoId={item['video_id']}"
            )