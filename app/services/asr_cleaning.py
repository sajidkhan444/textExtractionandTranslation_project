import re
from typing import List

def asr_cleaning(text: str) -> str:
    """
    Robust ASR cleaning for Whisper output.
    - Intelligently removes fillers without breaking grammar
    - Properly handles punctuation and sentence boundaries
    - Repairs fragments while maintaining natural flow
    - Restores proper English casing
    """
    
    # 1. Store original to preserve meaning
    if not text or not text.strip():
        return ""
    
    text = text.strip()
    
    # 2. Remove excessive whitespace first (tabs, multiple spaces, newlines)
    text = re.sub(r'\s+', ' ', text)
    
    # 3. Clean up punctuation - more intelligent handling
    # Normalize repeated punctuation (but preserve single punctuation)
    text = re.sub(r'([.,!?])\1+', r'\1', text)
    
    # Fix spacing around punctuation (remove spaces before, ensure space after)
    text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', text)
    
    # Remove punctuation that's incorrectly placed (e.g., standalone commas)
    text = re.sub(r'^[.,!?;:]\s*', '', text)
    text = re.sub(r'\s+[.,!?;:]\s*$', '', text)
    
    # 4. Remove fillers more intelligently (context-aware)
    # Define fillers with surrounding context patterns
    filler_patterns = [
        # Common filler words/phrases
        r'\b(um|uh|ah|eh|mm|hm)\b[.,!?;:]*\s*',
        r'\b(you\s+know|like|I\s+mean|kind\s+of|sort\s+of)\b[.,!?;:]*\s*',
        r'\b(okay|ok|right|so|well|anyway)\b[.,!?;:]*\s*(?=\band\b|\bbut\b|\bso\b|\bwell\b|\bokay\b)',  # At start of clause
        r'\b(yeah|yes|no)\b[.,!?;:]*\s*(?=\.|\?|!|,|$)',
        
        # Trailing fillers
        r'\s+\b(and\s+stuff|or\s+something|things\s+like\s+that|and\s+things)\b[.,!?;:]*',
        
        # Question/statement fillers
        r'\b(what\s+do\s+you\s+think|how\s+about|what\s+about)\b[.,!?;:]*\s*\?*',
    ]
    
    # Apply filler removal iteratively
    for pattern in filler_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # 5. Repair sentence fragments and common ASR errors
    repairs = [
        # Fix incomplete sentences
        (r'\b(Is|Are|Was|Were|Do|Does|Did|Can|Could|Will|Would|Should)\b\s*\.', r'\1?'),
        (r'\b(Is|Are|Was|Were|Do|Does|Did|Can|Could|Will|Would|Should)\b\s+that\s*\.', r'\1 that?'),
        
        # Fix common ASR mis-transcriptions
        (r'\b(the\s+the\b|\ba\s+a\b|\ban\s+an\b)', r'\1'),
        (r'\b(i\s+i\b|you\s+you\b|we\s+we\b|they\s+they\b)', r'\1'),
        
        # Fix repeated words (more robust pattern)
        (r'\b(\w+)(?:\s+\1\b)+', r'\1'),
        
        # Fix fragmented punctuation
        (r'\.\s+\.', '.'),
        (r',\s+,', ','),
        (r'\?\s+\?', '?'),
        (r'!\s+!', '!'),
        
        # Fix spacing issues with contractions
        (r'\s+\'\s*', '\''),
        (r'\'\s+s\b', '\'s'),
        
        # Fix common ASR artifacts
        (r'\b(can\s+you\s+see|do\s+you\s+see)\b[.,!?;:]*', ''),
        (r'\b(one\s+second|just\s+a\s+moment|hold\s+on)\b[.,!?;:]*', ''),
    ]
    
    for pattern, replacement in repairs:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # 6. Normalize whitespace again
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 7. Smart sentence splitting and reconstruction
    # First, ensure proper spacing after punctuation
    text = re.sub(r'([.!?])\s*', r'\1 ', text)
    text = re.sub(r'([,])\s*', r'\1 ', text)
    
    # Split into sentences (more robust than simple punctuation split)
    sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*$'
    sentences = re.split(sentence_endings, text)
    
    # Clean each sentence
    cleaned_sentences = []
    for sentence in sentences:
        if not sentence or not sentence.strip():
            continue
            
        sentence = sentence.strip()
        
        # Remove any remaining sentence-initial fillers
        sentence = re.sub(r'^(and|but|or|so|well|okay|ok|right|now|then)\b[.,!?;:]*\s*', '', sentence, flags=re.IGNORECASE)
        
        # Ensure sentence starts with capital letter
        if sentence and len(sentence) > 1:
            sentence = sentence[0].upper() + sentence[1:]
        
        # Ensure sentence ends with proper punctuation if it doesn't
        if sentence and sentence[-1] not in '.!?':
            # Check if it's a question
            if any(word in sentence.lower() for word in ['what', 'why', 'how', 'when', 'where', 'who', 'which', 'can', 'could', 'will', 'would', 'should']):
                sentence = sentence + '?'
            else:
                sentence = sentence + '.'
        
        cleaned_sentences.append(sentence)
    
    # 8. Join sentences with proper spacing
    text = ' '.join(cleaned_sentences)
    
    # 9. Final cleanup passes
    # Remove any orphaned punctuation
    text = re.sub(r'\s+[.,!?;:]+\s*$', '.', text)
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Ensure final punctuation
    if text and text[-1] not in '.!?':
        text = text + '.'
    
    return text