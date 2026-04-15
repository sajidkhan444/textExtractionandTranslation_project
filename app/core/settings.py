# # app/core/settings.py

# USE_DEMUCS = False          # Can disable later
# MAX_BATCH_SIZE = 8         # Safe for 24GB GPU
# BATCH_TIMEOUT = 4          # Seconds
# TARGET_SAMPLE_RATE = 16000


# app/core/settings.py

# Batch Collection
USE_DEMUCS = False
MAX_BATCH_SIZE = 8         
BATCH_TIMEOUT = 2.5        
TARGET_SAMPLE_RATE = 16000

# Whisper - Async Concurrent Processing
WHISPER_MAX_CONCURRENT = 4     # Max parallel Whisper tasks
# WHISPER_MAX_CONCURRENT = 2   # Use for smaller GPUs

# Qwen - Micro-batching
QWEN_MICRO_BATCH_SIZE = 4      # Batch size for keyword extraction
QWEN_BUFFER_TIMEOUT = 1.0      # Max wait time for batch (seconds)

# Translation - Micro-batching  
TRANSLATION_MICRO_BATCH_SIZE = 4   # Batch size for translation
TRANSLATION_BUFFER_TIMEOUT = 1.0   # Max wait time for batch (seconds)

# Webhook
WEBHOOK_MAX_RETRIES = 3
WEBHOOK_TIMEOUT = 30


