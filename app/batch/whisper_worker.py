# app/batch/whisper_worker.py


from app.batch.queue_manager import whisper_queue, qwen_queue
from app.services.asr_whisper import transcribe_batch
from app.services.normalization_qwen import normalize_batch
from app.core.logger import logger


async def whisper_worker():

    while True:

        data = await whisper_queue.get()

        batch = data["batch"]
        audio_paths = data["audio"]

        logger.info(f"🎙 Whisper batch received | size={len(batch)}")

        for item in batch:
            logger.info(f"🎙 Whisper processing started | videoId={item['video_id']}")

        transcriptions, timestamped = transcribe_batch(audio_paths)
        normalized = normalize_batch(transcriptions)

        for item, norm, ts in zip(batch, normalized, timestamped):
            item["normalized"] = norm
            item["timestamped"] = ts
            logger.info(f"✅ Whisper completed | videoId={item['video_id']}")

        await qwen_queue.put({
            "batch": batch
        })
