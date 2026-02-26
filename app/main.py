from fastapi import FastAPI, Response
import asyncio

from app.core.model_registry import load_all_models
from app.batch.batch_collector import batch_collector_worker
from app.batch.whisper_worker import whisper_worker
from app.batch.qwen_worker import qwen_worker
from app.batch.translation_worker import translation_worker
from app.api.routes import router


app = FastAPI(
    title="AI Processing API",
    description="Batch AI Processing System",
    version="1.0.0"
)

app.include_router(router)


# ✅ Root endpoint to avoid 404
@app.get("/")
async def root():
    return {
        "message": "API is running successfully 🚀",
        "docs_url": "/docs",
        "health_check": "/health"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "models_loaded": True,
        "queue_running": True
    }


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.on_event("startup")
async def startup():
    load_all_models()

    asyncio.create_task(batch_collector_worker())
    asyncio.create_task(whisper_worker())
    asyncio.create_task(qwen_worker())
    asyncio.create_task(translation_worker())