# app/api/routes.py

from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException
import uuid
import os
import subprocess
from app.batch.queue_manager import input_queue

router = APIRouter()

# 🔐 Change this to environment variable later
GPU_API_SECRET = "your_super_secret_key"


class JobRequest(BaseModel):
    videoId: str
    videoUrl: str
    language: str | None = "auto"


@router.post("/ai-services/jobs")
async def submit_job(
    data: JobRequest,
    x_api_key: str = Header(None)
):

    # 🔐 Security validation
    if x_api_key != GPU_API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    video_id = data.videoId
    video_url = data.videoUrl

    if not video_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")

    audio_path = f"temp_{uuid.uuid4()}.wav"

    try:

        # Extract audio (supports MP4 + HLS .m3u8)
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

        # Push to async batch pipeline
        await input_queue.put({
            "video_id": video_id,
            "temp_path": audio_path
        })

        # Immediate response (non-blocking)
        return {
            "status": "accepted",
            "videoId": video_id
        }

    except Exception as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)

        raise HTTPException(status_code=500, detail=str(e))



# @router.post("/process-from-url")
# async def process_from_url(data: VideoURLRequest):

#     video_url = data.video_url

#     if not video_url.startswith(("http://", "https://")):
#         return {"error": "Invalid URL"}

#     audio_path = f"temp_{uuid.uuid4()}.wav"

#     try:
#         # -------------------------------------------------
#         # Let FFMPEG handle both MP4 and HLS (.m3u8)
#         # -------------------------------------------------
#         subprocess.run([
#             "ffmpeg",
#             "-y",                      # overwrite if exists
#             "-i", video_url,           # input can be mp4 or m3u8
#             "-vn",                     # no video
#             "-acodec", "pcm_s16le",    # wav format
#             "-ar", "44100",
#             "-ac", "2",
#             audio_path
#         ], check=True)

#         # -------------------------------------------------
#         # Send audio to batch pipeline
#         # -------------------------------------------------
#         future = asyncio.get_event_loop().create_future()

#         await input_queue.put({
#             "temp_path": audio_path,
#             "future": future
#         })

#         result = await future

#         os.remove(audio_path)

#         return result

#     except Exception as e:
#         if os.path.exists(audio_path):
#             os.remove(audio_path)

#         return {"error": str(e)}