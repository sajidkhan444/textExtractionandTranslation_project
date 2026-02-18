# app/batch/whisper_worker.py

from app.batch.queue_manager import whisper_queue, qwen_queue
from app.services.whisper import transcribe_batch
from app.services.normalization import normalize_batch


async def whisper_worker():

    while True:

        data = await whisper_queue.get()

        batch = data["batch"]
        audio_paths = data["audio"]

        # Transcribe
        transcriptions, timestamped = transcribe_batch(audio_paths)

        # Normalize
        normalized = normalize_batch(transcriptions)

        # Attach results to original items
        for item, norm, ts in zip(batch, normalized, timestamped):
            item["normalized"] = norm
            item["timestamped"] = ts

        # Forward full batch (no parallel arrays)
        await qwen_queue.put({
            "batch": batch
        })
