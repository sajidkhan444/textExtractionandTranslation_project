from pydantic import BaseModel
import uuid
from fastapi import APIRouter
import asyncio
import os
import subprocess
from app.batch.queue_manager import input_queue


class VideoURLRequest(BaseModel):
    video_url: str


router = APIRouter()


@router.post("/process-from-url")
async def process_from_url(data: VideoURLRequest):

    video_url = data.video_url

    if not video_url.startswith(("http://", "https://")):
        return {"error": "Invalid URL"}

    audio_path = f"temp_{uuid.uuid4()}.wav"

    try:
        # -------------------------------------------------
        # Let FFMPEG handle both MP4 and HLS (.m3u8)
        # -------------------------------------------------
        subprocess.run([
            "ffmpeg",
            "-y",                      # overwrite if exists
            "-i", video_url,           # input can be mp4 or m3u8
            "-vn",                     # no video
            "-acodec", "pcm_s16le",    # wav format
            "-ar", "44100",
            "-ac", "2",
            audio_path
        ], check=True)

        # -------------------------------------------------
        # Send audio to batch pipeline
        # -------------------------------------------------
        future = asyncio.get_event_loop().create_future()

        await input_queue.put({
            "temp_path": audio_path,
            "future": future
        })

        result = await future

        os.remove(audio_path)

        return result

    except Exception as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return {"error": str(e)}
