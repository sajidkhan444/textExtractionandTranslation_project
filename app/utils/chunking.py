import re

def chunk_text_multilang(text, max_tokens=400):
    """
    Language-agnostic chunking for EN / ES / DE.
    Uses sentence boundaries + approximate token counting.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = ""
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = len(sentence.split())

        if current_tokens + sentence_tokens <= max_tokens:
            current_chunk += sentence + " "
            current_tokens += sentence_tokens
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            current_tokens = sentence_tokens

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
