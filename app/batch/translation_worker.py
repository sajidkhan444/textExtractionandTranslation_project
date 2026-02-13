# app/batch/translation_worker.py

from app.batch.queue_manager import translation_queue
from app.services.translation import translate_batch_multilang


async def translation_worker():

    while True:

        data = await translation_queue.get()

        batch = data["batch"]
        normalized = data["normalized"]
        timestamped = data["timestamped"]
        keywords_batch = data["keywords"]

        translations = translate_batch_multilang(normalized)

        for item, norm, ts, kws, trans in zip(
                batch,
                normalized,
                timestamped,
                keywords_batch,
                translations):

            item["future"].set_result({
                "english_normalized": norm,
                "timestamped": ts,
                "keywords": kws,
                "spanish_translation": trans["spanish_full"],
                "german_translation": trans["german_full"]
            })
