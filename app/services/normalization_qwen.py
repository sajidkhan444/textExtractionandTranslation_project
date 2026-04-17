# # app/services/normalization_qwen.py

# import torch
# from app.core.model_registry import models


# def normalize_batch(text_list):

#     tokenizer = models.qwen_tokenizer
#     model = models.qwen_model

#     messages_batch = []

#     for text in text_list:
#         messages = [
#            {
#             "role": "system",
#             "content": (
#                 "You are an English text normalizer and spell corrector, Your task is to convert ANY input text into clean, professional, grammatically correct written English.\n"
#                 "Rewrite spoken English into clear, grammatically correct and spell correctness written English.\n"
#                 "Preserve meaning exactly.\n"
#                 "Remove repetition, filler words, and disfluencies.\n\n"
#                 "CORRECT all spelling errors, typos, and incomplete words based on context\n"
#                 "EXPAND common abbreviations and shorthand (e.g., 's/w' → 'software', 'devlopr' → 'developer')\n"
                 
#                 "**EXAMPLES OF CORRECTIONS:**\n"
#                 "Input: 'I need a s/w developer with ML experince'\n"
#                 "Output: 'I need a software developer with machine learning experience'\n\n"
                               
#                 "Input: 'Mr. han is our team lead for AI projects'\n"
#                 "Output: 'Mr. Khan is our team lead for AI projects'\n\n"
                
#                 "Input: 'We use Pytorch for deep lernin models'\n"
#                 "Output: 'We use PyTorch for deep learning models'\n\n"
#                 "Rules:\n"
#                 "- Do NOT summarize\n"
#                 "- Do NOT translate\n"
#                 "- Do NOT add new information\n"
#                 "- Do NOT infer intent\n"
#                 "- Do NOT add emphasis\n"
#                 "- Rewrite conservatively\n"
#                 "- Output ONLY the rewritten text\n"
#                 "- Do NOT repeat instructions"
               

#             )
#         },
#             {"role": "user", "content": text}
#         ]

#         prompt = tokenizer.apply_chat_template(
#             messages,
#             tokenize=False,
#             add_generation_prompt=True
#         )

#         messages_batch.append(prompt)

#     inputs = tokenizer(
#         messages_batch,
#         padding=True,
#         truncation=True,
#         return_tensors="pt"
#     ).to(model.device)

#     with torch.no_grad():
#         outputs = model.generate(
#             **inputs,
#             max_new_tokens=600,
#             do_sample=False,
#             temperature=0.15,
#         )

#     decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)

#     cleaned = []

#     for text in decoded:
#         if "assistant" in text:
#             text = text.split("assistant")[-1].strip()
#         cleaned.append(text.strip())

#     return cleaned


# # app/services/normalization_qwen.py - ADD THIS

# def normalize_single(text):
#     """Normalize ONE text"""
#     tokenizer = models.qwen_tokenizer
#     model = models.qwen_model
    
#     messages = [
#         {
#             "role": "system",
#             "content": (
#                 "You are an English text normalizer and spell corrector..."
#                 # Your existing system prompt
#             )
#         },
#         {"role": "user", "content": text}
#     ]
    
#     prompt = tokenizer.apply_chat_template(
#         messages,
#         tokenize=False,
#         add_generation_prompt=True
#     )
    
#     inputs = tokenizer(
#         [prompt],  # Single item list
#         padding=True,
#         truncation=True,
#         return_tensors="pt"
#     ).to(model.device)
    
#     with torch.no_grad():
#         outputs = model.generate(
#             **inputs,
#             max_new_tokens=600,
#             do_sample=False,
#             temperature=0.15,
#         )
    
#     decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    
#     result = decoded[0]
#     if "assistant" in result:
#         result = result.split("assistant")[-1].strip()
    
#     return result


# app/services/normalization_qwen.py

import torch
from app.core.model_registry import models

# Define the system prompt once
SYSTEM_PROMPT = (
    "You are an English text normalizer and spell corrector, Your task is to convert ANY input text into clean, professional, grammatically correct written English.\n"
    "Rewrite spoken English into clear, grammatically correct and spell correctness written English.\n"
    "Preserve meaning exactly.\n"
    "Remove repetition, filler words, and disfluencies.\n\n"
    "CORRECT all spelling errors, typos, and incomplete words based on context\n"
    "EXPAND common abbreviations and shorthand (e.g., 's/w' → 'software', 'devlopr' → 'developer')\n"
    
    "**EXAMPLES OF CORRECTIONS:**\n"
    "Input: 'I need a s/w developer with ML experince'\n"
    "Output: 'I need a software developer with machine learning experience'\n\n"
    
    "Input: 'Mr. han is our team lead for AI projects'\n"
    "Output: 'Mr. Khan is our team lead for AI projects'\n\n"
    
    "Input: 'We use Pytorch for deep lernin models'\n"
    "Output: 'We use PyTorch for deep learning models'\n\n"
    
    "Rules:\n"
    "- Do NOT summarize\n"
    "- Do NOT translate\n"
    "- Do NOT add new information\n"
    "- Do NOT infer intent\n"
    "- Do NOT add emphasis\n"
    "- Rewrite conservatively\n"
    "- Output ONLY the rewritten text\n"
    "- Do NOT repeat instructions"
)

def _prepare_prompts(text_list):
    """Prepare chat prompts for a list of texts"""
    tokenizer = models.qwen_tokenizer
    prompts = []
    
    for text in text_list:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
        
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        prompts.append(prompt)
    
    return prompts

def _prepare_single_prompt(text):
    """Prepare chat prompt for a single text"""
    tokenizer = models.qwen_tokenizer
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]
    
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    return prompt

def _clean_output(text):
    """Clean the model output by removing 'assistant' prefix if present"""
    if "assistant" in text:
        text = text.split("assistant")[-1].strip()
    return text.strip()

def normalize_single(text):
    """Normalize a single text (for async pipeline)"""
    if not text or not text.strip():
        return ""
    
    tokenizer = models.qwen_tokenizer
    model = models.qwen_model
    
    # Prepare prompt
    prompt = _prepare_single_prompt(text)
    
    # Tokenize
    inputs = tokenizer(
        [prompt],  # Single item list
        padding=True,
        truncation=True,
        return_tensors="pt"
    ).to(model.device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=600,
            do_sample=False,
            temperature=0.15,
        )
    
    # Decode and clean
    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    cleaned = _clean_output(decoded[0])
    
    return cleaned

def normalize_batch(text_list):
    """Normalize a batch of texts"""
    if not text_list:
        return []
    
    tokenizer = models.qwen_tokenizer
    model = models.qwen_model
    
    # Prepare all prompts
    prompts = _prepare_prompts(text_list)
    
    # Tokenize batch
    inputs = tokenizer(
        prompts,
        padding=True,
        truncation=True,
        return_tensors="pt"
    ).to(model.device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=600,
            do_sample=False,
            temperature=0.15,
        )
    
    # Decode and clean
    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    cleaned = [_clean_output(text) for text in decoded]
    
    return cleaned