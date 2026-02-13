from fastapi import APIRouter, UploadFile, File
import asyncio
import shutil
import os
from app.batch.queue_manager import input_queue

router = APIRouter()

@router.post("/process")
async def process_audio(file: UploadFile = File(...)):

    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    future = asyncio.get_event_loop().create_future()

    await input_queue.put({
        "temp_path": temp_path,
        "future": future
    })

    result = await future

    os.remove(temp_path)

    return result
