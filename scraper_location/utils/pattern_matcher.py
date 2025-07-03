import os
import json
from scraper_location.config.constants import DIRECTION_WORDS

def extract_from_to(sentence: str, locs: list):
    """
    Extract (from, to) pair dari kalimat + daftar lokasi.
    """
    lower_sent = sentence.lower()
    words = lower_sent.split()

    if "dari" in words and "ke" in words:
        dari_idx = words.index("dari")
        ke_idx = words.index("ke")
        from_loc = _nearest_loc(words, dari_idx, locs)
        to_loc = _nearest_loc(words, ke_idx, locs)
        return {"from": from_loc, "to": to_loc, "reason": "explicit dari-ke"}

    for kw in DIRECTION_WORDS[1:]:
        if kw in words:
            kw_idx = words.index(kw)
            to_loc = _nearest_loc(words, kw_idx, locs)
            other_locs = [loc for loc in locs if loc != to_loc]
            from_loc = other_locs[0] if other_locs else None
            return {"from": from_loc, "to": to_loc, "reason": f"matched {kw}"}

    if len(locs) >= 2:
        return {"from": locs[0], "to": locs[1], "reason": "fallback pair"}

    return {"from": None, "to": None, "reason": "no pattern match"}

def _nearest_loc(words, idx, locs):
    """
    Ambil lokasi terdekat dengan index keyword.
    """
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

def handle_single_locations(locs):
    """
    Fallback untuk lokasi tunggal.
    """
    if len(locs) == 1:
        return {"location": locs[0], "reason": "single location fallback"}
    return None

def should_fallback_single(locs, result):
    """
    Cegah fallback single kalau pattern match mendeteksi pair tapi pair tidak valid.
    """
    if len(locs) >= 2 and not (result["from"] and result["to"]):
        # Ada 2 lokasi ➜ tapi pair tidak valid ➜ JANGAN fallback single
        return False
    return len(locs) == 1
