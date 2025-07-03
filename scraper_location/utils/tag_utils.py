from scraper_location.config.constants import DIRECTION_WORDS, WHITELIST_ACTIONS, IGNORED_LOCATION_TOKENS, CONTEXT_KEYWORDS, TRAFFIC_SUFFIXES
import json
import os
from scraper_location.core.logger import log_promote_jalan_result, log_promote_propn_result, log_promote_noun_result
from scraper_location.utils.text_cleaner import clean_and_split

def promote_directional_nouns(tags, validator, log_path="logs/promoted_tokens.jsonl"):
    os.makedirs("logs", exist_ok=True)
    new_tags = []
    log_entries = []

    for i, (word, tag) in enumerate(tags):
        if tag == "NOUN":
            for dir_word in DIRECTION_WORDS:
                if dir_word in word.lower():
                    parts = word.lower().split(dir_word)
                    location_part = parts[0].strip().title()
                    direction_part = dir_word

                    if location_part:
                        is_valid = validator.is_valid_location(location_part)
                        if is_valid:
                            new_tags.append((location_part, "LOCATION_PROMOTED"))
                            new_tags.append((direction_part, "NOUN"))
                        else:
                            new_tags.append((word, tag))  # fallback ke aslinya

                        # Log hasilnya
                        log_entries.append({
                            "token": location_part,
                            "tag": "NOUN",
                            "source": "promote_directional_nouns",
                            "promoted": is_valid,
                            "reason": "Validator accepted" if is_valid else "Validator rejected"
                        })
                        break  # sudah ketemu kata arah, keluar dari loop
            else:
                new_tags.append((word, tag))
        else:
            new_tags.append((word, tag))

    # 📝 Simpan log JSONL
    if log_entries:
        with open(log_path, "a", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return new_tags

def normalize_location_tags(tags, validator, log_path="logs/promoted_tokens.jsonl"):
    os.makedirs("logs", exist_ok=True)
    new_tags = []
    log_entries = []

    for word, tag in tags:
        lower_word = word.lower().strip()
        if "pendengar" in lower_word and ("ss" in lower_word or "suara surabaya" in lower_word):
            log_entries.append({
                "token": word,
                "tag": tag,
                "promoted": False,
                "reason": "Contains 'pendengar' and 'ss' or 'suara surabaya'"
            })
            new_tags.append((word, tag))  # Tidak dipromosikan
            continue
        if tag in {"PROPN", "PERSON"}:
            if validator.is_valid_location(word):
                new_tags.append((word, "LOCATION"))
                log_entries.append({
                    "token": word,
                    "tag": tag,
                    "promoted": True,
                    "reason": "Validator accepted"
                })
                continue
            else:
                log_entries.append({
                    "token": word,
                    "tag": tag,
                    "promoted": False,
                    "reason": "Validator rejected"
                })
        new_tags.append((word, tag))

    # Simpan log (append jsonl)
    if log_entries:
        with open(log_path, "a", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return new_tags

def split_location_with_status(tags, log_path="logs/split_tokens.jsonl"):
    """
    Pisahkan token seperti 'Jalan Praban MACET' → 'Jalan Praban' (LOCATION), 'MACET' (VERB).
    Log disimpan di logs/split_tokens.jsonl.
    """
    os.makedirs("logs", exist_ok=True)
    new_tags = []
    log_entries = []

    for word, tag in tags:
        lowered = word.lower()
        matched = next((kw for kw in WHITELIST_ACTIONS if lowered.endswith(kw)), None)

        if matched and " " in word:
            base = word.rsplit(" ", 1)[0]
            new_tags.append((base, "LOCATION"))
            new_tags.append((matched, "VERB"))  

            log_entries.append({
                "original_token": word,
                "original_tag": tag,
                "split_result": [
                    {"token": base, "tag": "LOCATION"},
                    {"token": matched, "tag": "VERB"}
                ],
                "reason": f"Ends with traffic keyword '{matched}'"
            })
        else:
            new_tags.append((word, tag))

    if log_entries:
        with open(log_path, "a", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return new_tags

import re

def promote_jalan_tokens(tags, validator):
    """
    Promote token yang mengandung 'jalan' atau 'jl.' ke LOCATION
    lalu cek validasi + log.
    """
    promoted = []
    for w, t in tags:
        wl = w.lower()
        if "jalan" in wl or "jl." in wl:
            result = validator.is_it_valid_location(w)
            is_valid = result[1]
            promoted.append((w, "LOCATION" if is_valid else t))
            log_promote_jalan_result(w, promoted[-1][1], is_valid)
            print(f"[DEBUG PROMOTE] word={w} -> tag={t} -> valid={is_valid} -> result={'LOCATION' if is_valid else t}")
        else:
            promoted.append((w, t))
    return promoted

def normalize_ignored_location_tokens(tags):
    """
    Jika token di IGNORED_LOCATION_TOKENS & tag-nya LOCATION,
    ubah ke O.
    """
    result = []
    for w, t in tags:
        if t == "LOCATION" and w.lower() in IGNORED_LOCATION_TOKENS:
            result.append((w, "O"))
        else:
            result.append((w, t))
    return result

def promote_propn_as_location(tags, validator):
    """
    Promote token bertag PROPN ke LOCATION
    hanya jika:
    - Valid di validator (dengan kata yang sudah di-clean)
    - DAN ada kata kontekstual di sekitar (2 token)
    """
    promoted = []
    for i, (w, t) in enumerate(tags):
        if t != "PROPN":
            promoted.append((w, t))
            continue
        # Konteks: cari token -2 s/d +2, exclude self
        window = []
        for offset in [-2, -1, 1, 2]:
            j = i + offset
            if 0 <= j < len(tags):
                window.append(tags[j][0].lower())

        context_hit = any(kw in window for kw in CONTEXT_KEYWORDS)
        _, is_valid, reason = validator.is_it_valid_location(w)

        promote = is_valid and context_hit
        promoted.append((w, "LOCATION" if promote else t))

        log_promote_propn_result(
            word=w,
            original_tag=t,
            valid=is_valid,
            reason=reason,
            context_hit=context_hit,
            result_tag="LOCATION" if promote else t
        )

    return promoted

def promote_valid_noun(tags, validator):
    """
    Promote NOUN ke LOCATION kalau valid (dengan kata yang sudah di-clean)
    """
    promoted = []
    for w, t in tags:
        if t == "NOUN" and len(w) >= 4:
            _, is_valid, reason = validator.is_it_valid_location(w)
            promoted.append((w, "LOCATION" if is_valid else t))
            log_promote_noun_result(w, "LOCATION" if is_valid else t, reason, is_valid)
        else:
            promoted.append((w, t))
    return promoted

def pre_clean_tokens(tags):
    """
    Pre-clean tokens: 
    - Pisahkan suffix traffic/direction menjadi token baru + tag.
    - Return list token baru.
    """
    cleaned = []
    for w, t in tags:
        base, extras = clean_and_split(w)
        for extra_token, extra_tag in extras:
            cleaned.append((extra_token, extra_tag))
        cleaned.append((base, t))
    return cleaned

def preprocess_location_tags(tags, validator):

    tags = split_location_with_status(tags)
    tags = normalize_location_tags(tags, validator)
    tags = promote_directional_nouns(tags, validator)
    return tags

def processing_location_tags(tags, validator):
    step0 = pre_clean_tokens(tags)
    step1 = promote_jalan_tokens(step0, validator)
    step2 = promote_propn_as_location(step1, validator)
    step3 = promote_valid_noun(step2, validator)
    step4 = normalize_ignored_location_tokens(step3)
    return step4
