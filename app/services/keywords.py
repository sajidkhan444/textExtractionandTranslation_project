# app/services/keywords.py

import torch
from app.utils.chunking import chunk_text_multilang
from app.core.model_registry import models


def _extract_keywords_batch(prompts):

    tokenizer = models.qwen_tokenizer
    model = models.qwen_model

    inputs = tokenizer(
        prompts,
        padding=True,
        truncation=True,
        max_length=1024,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=False,
            temperature=0.1,
            repetition_penalty=1.1,
        )

    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    cleaned_outputs = []

    for text in decoded:
        if "assistant" in text:
            text = text.split("assistant")[-1].strip()

        text = text.split("\n")[0].strip()

        keywords = [k.strip() for k in text.split("|") if k.strip()]

        seen = set()
        unique = []

        for k in keywords:
            low = k.lower()
            if low not in seen:
                seen.add(low)
                unique.append(k)

        cleaned_outputs.append(unique)

    return cleaned_outputs


def extract_keywords_batch_hybrid(normalized_texts, use_llm=True):

    batch_results = []

    for text in normalized_texts:

        chunks = chunk_text_multilang(text, max_tokens=350)
        chunk_prompts = []

        for chunk in chunks:

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You extract keywords from text.\n"
                        "Extract ONLY important skills, job titles, tools, technologies and professions "
                        "that are EXPLICITLY mentioned in the text.\n\n"
                        "STRICT RULES:\n"
                        "PRESERVE the original casing as it appears in the text.\n"
                        "Include common abbreviations AND their full forms if both appear.\n"
                        "- Output ONLY a pipe-separated list\n"
                        "- Use ONLY words or phrases that appear in the text\n"
                        "- Do NOT output category names\n"
                        "- Do NOT summarize\n"
                        "- Do NOT invent\n"
                        "- Do NOT generalize\n"
                        "- Do NOT explain\n"
                        "- Do NOT repeat\n"
                        "- Output ONE line only\n"
                    )
                },
                {"role": "user", "content": chunk}
            ]

            prompt = models.qwen_tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            chunk_prompts.append(prompt)

        if use_llm:
            try:
                llm_chunk_results = _extract_keywords_batch(chunk_prompts)

                merged = []
                seen = set()

                for kws in llm_chunk_results:
                    for k in kws:
                        low = k.lower()
                        if low not in seen:
                            seen.add(low)
                            merged.append(k)

                if len(merged) >= 3:
                    batch_results.append(merged)
                    continue

            except Exception as e:
                print("LLM chunk failed, fallback:", e)

        fallback = models.keybert_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=10,
            diversity=0.5
        )

        batch_results.append([kw for kw, _ in fallback])

    return batch_results
