# app/batch/demucs_worker.py

from app.batch.queue_manager import demucs_queue, whisper_queue
from app.services.asr_whisper import separate_vocals_batch
from app.core.settings import USE_DEMUCS


async def demucs_worker():

    while True:

        batch = await demucs_queue.get()

        file_paths = [item["temp_path"] for item in batch]

        if USE_DEMUCS:
            audio_arrays = separate_vocals_batch(file_paths)
        else:
            audio_arrays = file_paths

        await whisper_queue.put({
            "batch": batch,
            "audio": audio_arrays
        })
