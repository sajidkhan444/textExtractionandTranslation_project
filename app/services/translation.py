# app/services/translation.py

import torch
from app.utils.chunking import chunk_text_multilang
from app.core.model_registry import models


def _translate_batch(text_list, tokenizer, model):

    inputs = tokenizer(
        text_list,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(**inputs)

    return tokenizer.batch_decode(outputs, skip_special_tokens=True)


def translate_batch_multilang(normalized_texts):

    batch_results = []

    spanish_all_chunks = []
    german_all_chunks = []
    chunk_map = []

    for idx, text in enumerate(normalized_texts):
        chunks = chunk_text_multilang(text)

        for chunk in chunks:
            spanish_all_chunks.append(chunk)
            german_all_chunks.append(chunk)
            chunk_map.append(idx)

    spanish_translated = _translate_batch(
        spanish_all_chunks,
        models.mt_es_tokenizer,
        models.mt_es_model
    )

    german_translated = _translate_batch(
        german_all_chunks,
        models.mt_de_tokenizer,
        models.mt_de_model
    )

    user_spanish = {i: [] for i in range(len(normalized_texts))}
    user_german = {i: [] for i in range(len(normalized_texts))}

    for i, user_idx in enumerate(chunk_map):
        user_spanish[user_idx].append(spanish_translated[i])
        user_german[user_idx].append(german_translated[i])

    for i in range(len(normalized_texts)):
        batch_results.append({
            "spanish_full": "\n\n".join(user_spanish[i]),
            "german_full": "\n\n".join(user_german[i]),
        })

    return batch_results
