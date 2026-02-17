from fastapi import FastAPI
import asyncio

from app.core.model_registry import load_all_models
from app.batch.batch_collector import batch_collector_worker
#from app.batch.demucs_worker import demucs_worker
from app.batch.whisper_worker import whisper_worker
from app.batch.qwen_worker import qwen_worker
from app.batch.translation_worker import translation_worker
from app.api.routes import router   # 👈 ADD THIS

app = FastAPI()

app.include_router(router)  # 👈 ADD THIS


@app.on_event("startup")
async def startup():

    load_all_models()

    asyncio.create_task(batch_collector_worker())
    # asyncio.create_task(demucs_worker())
    asyncio.create_task(whisper_worker())
    asyncio.create_task(qwen_worker())
    asyncio.create_task(translation_worker())
