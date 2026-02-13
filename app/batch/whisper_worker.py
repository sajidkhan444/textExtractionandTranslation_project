# app/batch/whisper_worker.py

from app.batch.queue_manager import whisper_queue, qwen_queue
from app.services.asr_whisper import transcribe_batch
from app.services.asr_cleaning import asr_cleaning


async def whisper_worker():

    while True:

        data = await whisper_queue.get()

        batch = data["batch"]
        audio_arrays = data["audio"]

        full_texts, timestamped = transcribe_batch(audio_arrays)

        cleaned = [asr_cleaning(t) for t in full_texts]

        await qwen_queue.put({
            "batch": batch,
            "cleaned": cleaned,
            "timestamped": timestamped
        })
