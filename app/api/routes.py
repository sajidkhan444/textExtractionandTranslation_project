from fastapi import APIRouter, UploadFile, File
import asyncio
import shutil
import os
from app.batch.queue_manager import input_queue

router = APIRouter()

import subprocess

@router.post("/process")
async def process_audio(file: UploadFile = File(...)):

    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # ----------------------------
    # VIDEO → AUDIO AUTO CONVERT
    # ----------------------------
    if temp_path.endswith((".mp4", ".mov", ".mkv")):

        audio_path = temp_path.rsplit(".", 1)[0] + ".wav"

        subprocess.run([
            "ffmpeg",
            "-i", temp_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            audio_path
        ])

        os.remove(temp_path)
        temp_path = audio_path

    future = asyncio.get_event_loop().create_future()

    await input_queue.put({
        "temp_path": temp_path,
        "future": future
    })

    result = await future

    os.remove(temp_path)

    return result
