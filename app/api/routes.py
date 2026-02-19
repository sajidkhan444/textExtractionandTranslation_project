# app/api/routes.py

from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException
import uuid
import os
import subprocess
from app.batch.queue_manager import input_queue

router = APIRouter()

GPU_API_SECRET = os.getenv("GPU_API_SECRET")


class TranscriptionRequest(BaseModel):
    videoId: str
    videoUrl: str
    language: str | None = "auto"


@router.post("/ai-transcription")
async def submit_transcription(
    data: TranscriptionRequest,
    x_api_key: str = Header(None)
):

    if not GPU_API_SECRET:
        raise HTTPException(status_code=500, detail="Server secret not configured")

    if x_api_key != GPU_API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    video_id = data.videoId
    video_url = data.videoUrl

    if not video_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    audio_path = f"temp_{uuid.uuid4()}.wav"

    try:
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", video_url,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            audio_path
        ], check=True)

        await input_queue.put({
            "video_id": video_id,
            "temp_path": audio_path
        })

        return {
            "status": "accepted",
            "videoId": video_id
        }

    except Exception as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)

        raise HTTPException(status_code=500, detail=str(e))
