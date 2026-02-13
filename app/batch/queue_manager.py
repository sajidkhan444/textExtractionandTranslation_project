import asyncio

# Incoming user jobs
input_queue = asyncio.Queue()

# After batching
demucs_queue = asyncio.Queue()

# After demucs
whisper_queue = asyncio.Queue()

# After whisper
qwen_queue = asyncio.Queue()

# After qwen
translation_queue = asyncio.Queue()
