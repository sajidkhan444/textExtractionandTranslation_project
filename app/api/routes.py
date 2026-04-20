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

# AWS Body Schema Sends to GPU Server:
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


#New test End point

# ============= TEST ENDPOINT FOR DIRECT GPU PROCESSING (NO AWS) =============

# ============= TEST ENDPOINT FOR DIRECT GPU PROCESSING =============

from fastapi import UploadFile, File, Form
import uuid
import os
import subprocess

@router.post("/test-local")
async def test_local_transcription(
    video_file: UploadFile = File(...),
    language: str = Form("auto")
):
    """
    TEST ENDPOINT - Upload video directly to GPU server.
    """
    logger.info(f"🧪 TEST: Direct upload | file={video_file.filename}")
    
    # Generate unique IDs
    video_id = f"test-{uuid.uuid4().hex[:8]}"
    
    # Use absolute paths
    base_dir = "/workspace/project"
    temp_video = os.path.join(base_dir, f"temp_video_{video_id}.mp4")
    temp_audio = os.path.join(base_dir, f"temp_audio_{video_id}.wav")
    
    try:
        # 1. Save uploaded video
        content = await video_file.read()
        with open(temp_video, "wb") as f:
            f.write(content)
        
        logger.info(f"📁 Video saved | videoId={video_id} | size={len(content)} bytes | path={temp_video}")
        
        # 2. Extract audio using ffmpeg
        logger.info(f"🎬 Extracting audio | videoId={video_id}")
        
        # Check if ffmpeg works
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_video,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            temp_audio
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception(f"Audio extraction failed: {result.stderr}")
        
        # Check if audio file was created
        if not os.path.exists(temp_audio):
            raise Exception(f"Audio file not created: {temp_audio}")
        
        audio_size = os.path.getsize(temp_audio)
        logger.info(f"✅ Audio extracted | videoId={video_id} | size={audio_size} bytes | path={temp_audio}")
        
        # 3. Queue for pipeline processing
        from app.batch.queue_manager import input_queue
        await input_queue.put({
            "video_id": video_id,
            "temp_path": temp_audio  # Use full path
        })
        
        logger.info(f"📦 Job queued | videoId={video_id} | queue_size={input_queue.qsize()}")
        
        # 4. Clean up video file (keep audio for processing)
        if os.path.exists(temp_video):
            os.remove(temp_video)
            logger.info(f"🗑️ Temp video removed | videoId={video_id}")
        
        # 5. Return immediate response
        return {
            "status": "accepted",
            "videoId": video_id,
            "filename": video_file.filename,
            "language": language,
            "audio_path": temp_audio,
            "message": f"Video queued. Check logs: tail -f /workspace/project/logs/fastapi.out.log | grep {video_id}"
        }
        
    except Exception as e:
        logger.error(f"❌ Test endpoint error | videoId={video_id} | error={str(e)}")
        
        # Cleanup on error
        for path in [temp_video, temp_audio]:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"🗑️ Cleaned up: {path}")
        
        return {
            "status": "error",
            "videoId": video_id,
            "error": str(e)
        }


@router.get("/queue-status")
async def queue_status():
    """Check queue sizes and worker status"""
    from app.batch.queue_manager import input_queue, whisper_queue, qwen_queue, translation_queue
    
    return {
        "input_queue_size": input_queue.qsize(),
        "whisper_queue_size": whisper_queue.qsize(),
        "qwen_queue_size": qwen_queue.qsize(),
        "translation_queue_size": translation_queue.qsize(),
        "workers_running": True,
        "note": "If input_queue > 0 and other queues = 0, workers may be stuck"
    }