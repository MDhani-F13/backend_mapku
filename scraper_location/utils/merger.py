from typing import List, Tuple
from scraper_location.config.constants import IGNORED_LOCATION_TOKENS, LOCATION_KEYWORDS, WHITELIST_ACTIONS, IGNORED_ENTITY_PHRASES
from fuzzywuzzy import fuzz
from scraper_location.core.logger import log_merge_adjacent_result

def merge_pos_ner(pos_results: List[dict], ner_results: List[dict]) -> List[Tuple[str, str]]:
    """Gabungkan hasil POS dan NER ke satu daftar (word, tag)."""
    merged = []
    for pos_item in pos_results:
        word = pos_item["word"]
        tag = pos_item["tag"]
        ner_tag = tag  

        for ner_item in ner_results:
            ner_text = ner_item["text"]
            ner_entity = ner_item["entity"]
            word_clean = word.lower().replace(" ", "")
            ner_clean = ner_text.lower().replace(" ", "")
            if word_clean in ner_clean or ner_clean in word_clean:
                ner_tag = ner_entity
                break

        merged.append((word, ner_tag))
    return merged

def is_likely_location(phrase: str) -> bool:
    """Deteksi apakah frasa kemungkinan nama jalan/lokasi."""
    phrase = phrase.lower()
    return any(keyword in phrase for keyword in LOCATION_KEYWORDS)

def merge_adjacents_locations(tags, validator):
    merged = []
    buffer = []

    def flush_buffer():
        nonlocal buffer
        if not buffer:
            return

        joined = ' '.join(buffer)
        combined_result = validator.is_it_valid_location(joined)
        combined_valid = combined_result[1]

        parts_valid = []
        for part in buffer:
            part_result = validator.is_it_valid_location(part)
            parts_valid.append({
                "part": part,
                "valid": part_result[1]
            })

        log_merge_adjacent_result(buffer, combined_valid, parts_valid)

        if combined_valid:
            merged.append((joined, "LOCATION"))
        else:
            for p in parts_valid:
                if p["valid"]:
                    merged.append((p["part"], "LOCATION"))
                else:
                    merged.append((p["part"], "O"))

        buffer.clear()

    for w, t in tags:
        wl = w.lower()

        if t == "LOCATION":
            if wl in IGNORED_LOCATION_TOKENS:
                flush_buffer()
                merged.append((w, "O"))  
            else:
                buffer.append(w)
        else:
            flush_buffer()
            merged.append((w, t))

    flush_buffer()
    return merged

