# app/services/asr_whisper.py

from app.core.model_registry import models
import torch
import torchaudio.transforms as T
import soundfile as sf
from demucs.apply import apply_model
from app.core.settings import TARGET_SAMPLE_RATE


# ----------------------------
# BATCHED DEMUCS
# ----------------------------

def separate_vocals_batch(file_paths):

    device = models.audio_device
    outputs = []

    for path in file_paths:

        wav, sr = sf.read(path)
        wav = torch.from_numpy(wav).float()

        if wav.dim() == 1:
            wav = wav.unsqueeze(0)

        if wav.shape[0] == 1:
            wav = torch.cat([wav, wav], dim=0)

        if sr != TARGET_SAMPLE_RATE:
            resampler = T.Resample(sr, TARGET_SAMPLE_RATE)
            wav = resampler(wav)

        with torch.no_grad():
            sources = apply_model(
                models.demucs_model,
                wav.unsqueeze(0).to(device),
                device=device,
                shifts=1,          # reduced
                split=True,
                overlap=0.1,       # reduced
                progress=False
            )

        vocals = sources[0, 3].mean(dim=0)
        outputs.append(vocals.cpu().numpy())

        torch.cuda.empty_cache()

    return outputs



# ----------------------------
# BATCHED WHISPER
# ----------------------------

def transcribe_batch(audio_arrays):

    results = models.asr_pipeline(
        audio_arrays,
        batch_size=min(len(audio_arrays), 6),
        return_timestamps=True,
    )

    full_texts = []
    timestamped_texts = []

    for result in results:
        full_texts.append(result["text"].strip())

        lines = []
        for chunk in result.get("chunks", []):
            start = int(chunk["timestamp"][0])
            m = start // 60
            s = start % 60
            lines.append(f"({m}:{s:02d}) {chunk['text'].strip()}")

        timestamped_texts.append("\n".join(lines))

    return full_texts, timestamped_texts
