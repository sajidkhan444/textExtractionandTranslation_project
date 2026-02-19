# app/api/routes.py


#GPU receives videoUrl
#GPU pulls video from that URL
#GPU processes internally
#GPU sends result to AWS webhook
#  No direct file upload.
#  No persistent link between intake and callback except videoId.
#  videoId is the correlation key.


from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException
import uuid
import os
import subprocess
from app.batch.queue_manager import input_queue
from app.core.logger import logger

router = APIRouter()

GPU_API_SECRET = os.getenv("GPU_API_SECRET")

# AWS Body Schema Ssends to GPU Server:
class TranscriptionRequest(BaseModel):
    videoId: str
    #GPU Pulls the data from the videoUrl
    videoUrl: str
    language: str | None = "auto"


@router.post("/ai-transcription")
async def submit_transcription(
    data: TranscriptionRequest,
    x_api_key: str = Header(None)
):

    logger.info(f"📥 Incoming job request | videoId={data.videoId}")

    if not GPU_API_SECRET:
        logger.error("❌ GPU_API_SECRET not configured on server")
        raise HTTPException(status_code=500, detail="Server secret not configured")

    if x_api_key != GPU_API_SECRET:
        logger.warning(f"🚫 Unauthorized request | videoId={data.videoId}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    video_id = data.videoId
    video_url = data.videoUrl

    if not video_url.startswith(("http://", "https://")):
        logger.error(f"❌ Invalid URL received | videoId={video_id}")
        raise HTTPException(status_code=400, detail="Invalid URL")

    audio_path = f"temp_{uuid.uuid4()}.wav"

        #When AWS calls /ai-transcription:
    #The GPU does NOT manually download the video first.
    #FFmpeg directly reads from:
    #https://cloudfront-url.m3u8
#So:

#AWS → sends public URL
#GPU → ffmpeg pulls video stream directly
#No separate download API.

    try:
        logger.info(f"🎬 Starting audio extraction | videoId={video_id}")

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

        logger.info(f"📦 Audio extracted and queuing job | videoId={video_id}")

#After Conversion the video strem
#The below code will forward the stream to queue manager
        await input_queue.put({
            "video_id": video_id,
            "temp_path": audio_path
        })

        logger.info(f"✅ Job accepted and queued | videoId={video_id}")
#4️⃣ What GPU Sends Back To AWS
#GPU DOES NOT return result in same request.
#It return immediatly the below body
        return {
            "status": "accepted",
            "videoId": video_id
        }
    #Then processing async start 

    except Exception as e:
        logger.error(f"🔥 Processing failed at intake | videoId={video_id} | error={str(e)}")

        if os.path.exists(audio_path):
            os.remove(audio_path)

        raise HTTPException(status_code=500, detail=str(e))
