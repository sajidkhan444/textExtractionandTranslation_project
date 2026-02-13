import torch
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForCausalLM,
    MarianMTModel,
    MarianTokenizer
)
from demucs.pretrained import get_model
from keybert import KeyBERT


class ModelRegistry:

    def __init__(self):

        self.cuda_available = torch.cuda.is_available()

        if self.cuda_available:
            self.audio_device = torch.device("cuda:0")   # Demucs + Whisper
            self.llm_device = torch.device("cuda:1")     # Qwen + MT
            self.dtype = torch.float16
        else:
            self.audio_device = torch.device("cpu")
            self.llm_device = torch.device("cpu")
            self.dtype = torch.float32

        # ASR
        self.asr_pipeline = None
        self.demucs_model = None

        # Qwen
        self.qwen_tokenizer = None
        self.qwen_model = None

        # Translation
        self.mt_es_tokenizer = None
        self.mt_es_model = None
        self.mt_de_tokenizer = None
        self.mt_de_model = None

        # Keywords
        self.keybert_model = None


models = ModelRegistry()


def load_all_models():

    print("🚀 Loading models into registry...")

    # ------------------ ASR ------------------

    ASR_MODEL_ID = "distil-whisper/distil-large-v3.5"

    models.asr_pipeline = pipeline(
        task="automatic-speech-recognition",
        model=ASR_MODEL_ID,
        device=0 if models.cuda_available else -1,
        torch_dtype=models.dtype,
    )

    models.demucs_model = get_model(name="htdemucs")
    models.demucs_model.to(models.audio_device)
    models.demucs_model.eval()

    print("✅ Whisper + Demucs loaded on CUDA:0")

    # ------------------ QWEN ------------------

    QWEN_MODEL = "Qwen/Qwen2.5-3B-Instruct"

    models.qwen_tokenizer = AutoTokenizer.from_pretrained(
        QWEN_MODEL,
        trust_remote_code=True
    )

    models.qwen_model = AutoModelForCausalLM.from_pretrained(
        QWEN_MODEL,
        torch_dtype=models.dtype,
        trust_remote_code=True
    ).to(models.llm_device)

    print("✅ Qwen loaded on CUDA:1")

    # ------------------ TRANSLATION ------------------

    es_name = "Helsinki-NLP/opus-mt-en-es"
    models.mt_es_tokenizer = MarianTokenizer.from_pretrained(es_name)
    models.mt_es_model = MarianMTModel.from_pretrained(es_name).to(models.llm_device)

    de_name = "Helsinki-NLP/opus-mt-en-de"
    models.mt_de_tokenizer = MarianTokenizer.from_pretrained(de_name)
    models.mt_de_model = MarianMTModel.from_pretrained(de_name).to(models.llm_device)

    print("✅ Marian MT loaded on CUDA:1")

    # ------------------ KEYBERT ------------------

    models.keybert_model = KeyBERT("sentence-transformers/all-mpnet-base-v2")

    print("✅ KeyBERT loaded")

    print("🔥 All models loaded successfully")
