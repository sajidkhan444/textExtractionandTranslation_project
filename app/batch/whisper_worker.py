# app/batch/whisper_worker.py

from app.batch.queue_manager import whisper_queue, qwen_queue
from app.services.asr_whisper import transcribe_batch
from app.services.normalization_qwen import normalize_batch
from app.services.asr_whisper import transcribe_single  # NEW: individual function
from app.services.normalization_qwen import normalize_single  # NEW: individual function
from app.core.logger import logger
from app.core.settings import WHISPER_MAX_CONCURRENT
import asyncio


# async def whisper_worker():

#     while True:

#         data = await whisper_queue.get()

#         batch = data["batch"]
#         audio_paths = data["audio"]

#         logger.info(f"🎙 Whisper batch received | size={len(batch)}")

#         for item in batch:
#             logger.info(f"🎙 Whisper processing started | videoId={item['video_id']}")

#         transcriptions, timestamped = transcribe_batch(audio_paths)
#         normalized = normalize_batch(transcriptions)

#         for item, norm, ts in zip(batch, normalized, timestamped):
#             item["normalized"] = norm
#             item["timestamped"] = ts
#             logger.info(f"✅ Whisper completed | videoId={item['video_id']}")

#         await qwen_queue.put({
#             "batch": batch
#         })

WHISPER_MAX_CONCURRENT = 4  # Process up to 4 samples simultaneously


async def whisper_worker():

    # Track running tasks
    running_tasks = set()
    
    while True:

        data = await whisper_queue.get()

        full_batch = data["batch"]
        full_audio_paths = data["audio"]

        logger.info(f"🎙 Whisper batch received | size={len(full_batch)}")

        # Launch EACH sample as independent async task
        for audio_path, item in zip(full_audio_paths, full_batch):
            
            # Wait if we have too many concurrent tasks
            while len(running_tasks) >= WHISPER_MAX_CONCURRENT:
                done, running_tasks = await asyncio.wait(
                    running_tasks, 
                    return_when=asyncio.FIRST_COMPLETED
                )
            
            # Create independent task for this sample
            task = asyncio.create_task(
                _process_single_sample(audio_path, item)
            )
            running_tasks.add(task)
            
            # Clean up completed tasks
            task.add_done_callback(running_tasks.discard)
        
        # Wait for all tasks in this batch to complete
        if running_tasks:
            await asyncio.gather(*running_tasks)
            running_tasks.clear()


async def _process_single_sample(audio_path, item):
    """Process ONE sample independently - doesn't wait for others"""
    
    logger.info(f"🎙 Whisper processing started | videoId={item['video_id']}")
    
    # Process single audio file
    transcription, timestamped = transcribe_single(audio_path)  # Individual function
    normalized = normalize_single(transcription)  # Individual function
    
    item["normalized"] = normalized
    item["timestamped"] = timestamped
    
    logger.info(f"✅ Whisper completed | videoId={item['video_id']}")
    
    # IMMEDIATELY send to next stage (no waiting for batch mates)
    await qwen_queue.put({"sample": item})

        
