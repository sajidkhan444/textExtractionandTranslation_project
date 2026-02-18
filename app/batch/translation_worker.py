# app/batch/translation_worker.py

import os
import requests
from app.batch.queue_manager import translation_queue
from app.services.translation import translate_batch_multilang

#AWS end point

AWS_WEBHOOK_URL = "http://localhost:5500/ai-services/webhooks/transcription"
WEBHOOK_SECRET = "3f9b7c8e2a4d6f1b9c0e7a2d4f8c1b6a"


async def translation_worker():

    while True:

        data = await translation_queue.get()

        batch = data["batch"]

        texts = [item["normalized"] for item in batch]

        translations = translate_batch_multilang(texts)

        for item, trans in zip(batch, translations):

            payload = {
                "videoId": item["video_id"],
                "transcription": item["normalized"],
                "summary": item["normalized"][:500],
                "keywords": item["keywords"],
                "translation": trans["spanish_full"]
            }

            # Retry mechanism (safe production practice)
            for attempt in range(3):
                try:
                    requests.post(
                        AWS_WEBHOOK_URL,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "x-webhook-secret": WEBHOOK_SECRET
                        },
                        timeout=30
                    )
                    break
                except Exception as e:
                    print(f"Webhook retry {attempt+1} failed:", e)

            # Cleanup audio file
            if os.path.exists(item["temp_path"]):
                os.remove(item["temp_path"])
