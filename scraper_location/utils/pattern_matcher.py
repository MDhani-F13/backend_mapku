import os
import json
from scraper_location.config.constants import DIRECTION_WORDS

def extract_from_to(sentence: str, locs: list):
    """
    FINAL: Extract (from, to) pair dengan robust direction word window & nearest logic.
    """
    lower_sent = sentence.lower()
    words = lower_sent.split()

    # 1️⃣ dari–ke
    if "dari" in words and "ke" in words:
        dari_idx = words.index("dari")
        ke_idx = words.index("ke")
        if dari_idx < ke_idx:
            from_loc = _next_loc_window(words, dari_idx, locs, window=4) or _nearest_loc(words, dari_idx, locs)
            to_loc = _next_loc_window(words, ke_idx, locs, window=4) or _nearest_loc(words, ke_idx, locs)
        else:
            # kebalik ➜ swap
            to_loc = _next_loc_window(words, ke_idx, locs, window=4) or _nearest_loc(words, ke_idx, locs)
            from_loc = _next_loc_window(words, dari_idx, locs, window=4) or _nearest_loc(words, dari_idx, locs)
        if from_loc and to_loc and from_loc != to_loc:
            return {"from": from_loc, "to": to_loc, "reason": "explicit dari-ke"}
        else:
            return {"from": None, "to": None, "reason": "dari-ke but same"}

    # 2️⃣ direction word robust
    for kw in DIRECTION_WORDS[1:]:
        if kw in words:
            kw_idx = words.index(kw)

            before = _prev_loc_window(words, kw_idx, locs, window=4)
            after = _next_loc_window(words, kw_idx, locs, window=4)

            from_loc = before
            to_loc = after

            if not from_loc:
                from_loc = _nearest_loc_before(words, kw_idx, locs)
            if not to_loc:
                to_loc = _nearest_loc_after(words, kw_idx, locs)

            if from_loc and to_loc and from_loc != to_loc:
                return {"from": from_loc, "to": to_loc, "reason": f"matched {kw}"}
            else:
                return {"from": None, "to": None, "reason": f"matched {kw} but same"}

    # 3️⃣ fallback pair loc >= 2 with context
    if len(locs) >= 2:
        if any(kw in words for kw in ["ditutup", "pengalihan", "rekayasa"]):
            from_loc = locs[0]
            to_loc = locs[1]
            if from_loc != to_loc:
                return {"from": from_loc, "to": to_loc, "reason": "fallback pair"}
            else:
                return {"from": None, "to": None, "reason": "fallback pair but same"}

    # 4️⃣ multi-loc fallback if >2 and traffic jam context
    if len(locs) > 2 and any(kw in lower_sent for kw in ["macet", "padat", "lumpuh"]):
        return {"from": None, "to": None, "reason": "multi-loc fallback"}

    # 5️⃣ single fallback
    if len(locs) == 1:
        return {"from": None, "to": None, "reason": "single"}

    return {"from": None, "to": None, "reason": "no match"}


def _next_loc_window(words, idx, locs, window=4):
    next_words = words[idx+1: idx+1+window]
    for loc in locs:
        tokens = loc.lower().split()
        if all(token in next_words for token in tokens):
            return loc
    return None

def _prev_loc_window(words, idx, locs, window=4):
    prev_words = words[max(0, idx-window): idx]
    for loc in locs:
        tokens = loc.lower().split()
        if all(token in prev_words for token in tokens):
            return loc
    return None

def _nearest_loc(words, idx, locs):
    min_dist = float('inf')
    best = None
    for loc in locs:
        for token in loc.lower().split():
            if token in words:
                dist = abs(words.index(token) - idx)
                if dist < min_dist:
                    min_dist = dist
                    best = loc
    return best

def _nearest_loc_before(words, idx, locs):
    min_dist = float('inf')
    best = None
    for loc in locs:
        for token in loc.lower().split():
            if token in words:
                token_idx = words.index(token)
                if token_idx < idx:
                    dist = abs(token_idx - idx)
                    if dist < min_dist:
                        min_dist = dist
                        best = loc
    return best

def _nearest_loc_after(words, idx, locs):
    min_dist = float('inf')
    best = None
    for loc in locs:
        for token in loc.lower().split():
            if token in words:
                token_idx = words.index(token)
                if token_idx > idx:
                    dist = abs(token_idx - idx)
                    if dist < min_dist:
                        min_dist = dist
                        best = loc
    return best

def handle_single_locations(locs):
    if len(locs) == 1:
        return {"location": locs[0], "reason": "single location fallback"}
    return None

def should_fallback_single(locs, result):
    if len(locs) >= 2 and not (result["from"] and result["to"]):
        return False
    return len(locs) == 1

def check_multi_loc_fallback(sentence: str, locs: list):
    multi_kw = ["macet", "padat", "lumpuh", "tidak bergerak"]
    if any(kw in sentence.lower() for kw in multi_kw):
        singles = []
        for loc in locs:
            singles.append({
                "location": loc,
                "reason": "multi-loc fallback",
                "sentence": sentence
            })
        return singles
    return []
