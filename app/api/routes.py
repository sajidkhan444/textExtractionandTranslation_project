from pydantic import BaseModel
import requests
import uuid

from fastapi import APIRouter, UploadFile, File
import asyncio
import shutil
import os
from app.batch.queue_manager import input_queue


class VideoURLRequest(BaseModel):
    video_url: str


router = APIRouter()

import subprocess

@router.post("/process-from-url")
async def process_from_url(data: VideoURLRequest):

    video_url = data.video_url

    if not video_url.startswith(("http://", "https://")):
        return {"error": "Invalid URL"}

    temp_path = f"temp_{uuid.uuid4()}.mp4"

    try:
        # Download video
        response = requests.get(video_url, stream=True, timeout=120)
        response.raise_for_status()

        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Convert if video
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
            ], check=True)

            os.remove(temp_path)
            temp_path = audio_path

        # Send to pipeline
        future = asyncio.get_event_loop().create_future()

        await input_queue.put({
            "temp_path": temp_path,
            "future": future
        })

        result = await future

        os.remove(temp_path)

        return result

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {"error": str(e)}
