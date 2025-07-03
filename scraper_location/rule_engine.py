import re, os, json
from scraper_location.core.logger import log_step2_from_to, log_step3_enrich_result
from scraper_location.utils.pattern_matcher import extract_from_to, handle_single_locations, should_fallback_single
from scraper_location.utils.tag_utils import processing_location_tags
from scraper_location.utils.merger import merge_adjacents_locations
from scraper_location.utils.location_snapper import snap_location_pair, is_area
from traffic.utils import can_make_directions_call
from traffic.models import TrafficSegment
from scraper_location.utils.google_client import get_directions_polyline
from dateutil import parser
import os
import json
import re
from dateutil import parser

def check_rules_step1(merged_tags, validator, tweet_obj=None):
    """
    STEP 1:
    - promote + merge + clean
    - split sentence
    - attach original split for info
    """
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/check_rules_step1.jsonl"

    # 1) Normalisasi & merge
    normalized = processing_location_tags(merged_tags, validator)
    merged = merge_adjacents_locations(normalized, validator)

    # 2) Validasi final
    cleaned = []
    for w, t in merged:
        if t == "LOCATION":
            result = validator.is_it_valid_location(w)
            valid = result[1]
            if not valid:
                cleaned.append((w, "O"))
            else:
                cleaned.append((w, t))
        else:
            cleaned.append((w, t))

    # 3) Split kalimat by token cleaned
    sentences = []
    sent = []
    for w, t in cleaned:
        sent.append((w, t))
        if w in {".", ";"}:
            sentences.append(sent)
            sent = []
    if sent:
        sentences.append(sent)

    # 4) Juga split kalimat dari original tweet_text
    original_text = tweet_obj.get("cleaned_text") if tweet_obj else ""
    # Paling aman: split di ";", lalu strip spasi
    original_sents = [s.strip() for s in original_text.split(";") if s.strip()]

    # 5) Gabungkan info
    all_locations = []
    sentences_info = []
    for idx, sent_tokens in enumerate(sentences):
        locs = [w for w, t in sent_tokens if t == "LOCATION"]
        all_locations.extend(locs)
        cleaned_sentence = ' '.join(w for w, t in sent_tokens)

        # Gunakan original jika ada indexnya, else fallback ""
        original = original_sents[idx] if idx < len(original_sents) else ""

        sentences_info.append({
            "sentence": cleaned_sentence,
            "locations": locs,
            "original_sentence": original
        })

    # 6) Ambil time
    times = [w for w, t in merged if t == "TIME" and re.search(r"\d{1,2}\.\d{2}", w)]
    if not times and tweet_obj and "created_at" in tweet_obj:
        dt = parser.parse(tweet_obj["created_at"])
        times = [dt.strftime("%H.%M")]

    # 7) Buat output
    info = {
        "tweet_text": original_text,
        "time": times[0] if times else None,
        "locations": all_locations,
        "sentences": sentences_info
    }

    # 8) Log
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")

    return info

def check_rules_step2(step1_info):
    """
    STEP 2 FINAL:
    - Proses sentence by sentence
    - Cari from-to
    - Fallback single hanya jika murni single
    - Log detail
    """

    segments = []
    singles = []

    for sent in step1_info["sentences"]:
        sentence = sent["sentence"]
        locs = sent["locations"]

        result = extract_from_to(sentence, locs)

        log_step2_from_to(sentence, locs, result["from"], result["to"], result["reason"])

        if result["from"] and result["to"]:
            segments.append({
                "from": result["from"],
                "to": result["to"],
                "reason": result["reason"],
                "sentence": sentence
            })
        elif should_fallback_single(locs, result):
            single = handle_single_locations(locs)
            if single:
                if is_area(single["location"]):
                    print(f"[STEP2] ⚠️ Single location '{single['location']}' terdeteksi major area ➜ SKIP fallback.")
                else:
                    single["sentence"] = sentence
                    singles.append(single)
        else:
            print(f"[STEP2] Pair fail, skip fallback single ➜ sentence='{sentence}' | locs={locs}")

    output = {
        "segments": segments,
        "single_locations": singles
    }

    return output


def check_rules_step3(step2_info, validator, auto_fallback=True):
    """
    STEP 3 FINAL:
    - Ambil lat/lng dari cache
    - Snap ke simpang kalau area terlalu luas (pakai snap_location_pair)
    - Buat route polyline pakai Directions API
    - Single: hanya lat/lng, tidak snap
    - Log ke logs/step3_enrich.jsonl
    """

    os.makedirs("logs", exist_ok=True)

    segments_with_coords = []
    singles_with_coords = []

    def get_coords(loc):
        key = validator._hash_key(loc.lower())

        # Refresh cache
        if os.path.exists(validator.cache_file):
            with open(validator.cache_file, "r", encoding="utf-8") as f:
                validator.cache = json.load(f)

        if key in validator.cache:
            data = validator.cache[key]
            lat = data.get("lat")
            lng = data.get("lng")

            if (lat is None or lng is None) and auto_fallback:
                _, valid, _ = validator.google_check_location(loc)
                data = validator.cache[key]
                lat = data.get("lat")
                lng = data.get("lng")

            return lat, lng

        if auto_fallback:
            _, valid, _ = validator.google_check_location(loc)
            data = validator.cache.get(key, {})
            return data.get("lat"), data.get("lng")

        return None, None

    # === SEGMENTS ===
    for seg in step2_info["segments"]:
        lat_from, lng_from = get_coords(seg["from"])
        lat_to, lng_to = get_coords(seg["to"])

        # 💡 SNAP di sini
        new_from, new_to = snap_location_pair(
            seg["from"], seg["to"],
            lat_from, lng_from,
            lat_to, lng_to
        )

        route_polyline = None
        if new_from["lat"] and new_from["lng"] and new_to["lat"] and new_to["lng"]:
            if can_make_directions_call():
                route_polyline = get_directions_polyline(
                    new_from["lat"], new_from["lng"],
                    new_to["lat"], new_to["lng"]
                )
            else:
                print("❌ Directions API quota limit reached. Skip polyline.")

        entry = {
            "from": new_from["location"],
            "to": new_to["location"],
            "reason": seg["reason"],
            "sentence": seg.get("sentence", ""),
            "from_lat": new_from["lat"],
            "from_lng": new_from["lng"],
            "to_lat": new_to["lat"],
            "to_lng": new_to["lng"],
            "route_polyline": route_polyline
        }

        log_step3_enrich_result(entry)
        segments_with_coords.append(entry)

    # === SINGLE ===
    for single in step2_info["single_locations"]:
        lat, lng = get_coords(single["location"])
        entry = {
            "location": single["location"],
            "reason": single["reason"],
            "sentence": single.get("sentence", ""),
            "lat": lat,
            "lng": lng
        }
        log_step3_enrich_result(entry)
        singles_with_coords.append(entry)

    return {
        "segments": segments_with_coords,
        "single_locations": singles_with_coords
    }


def get_or_cache_directions_polyline(segment):
    if segment.route_polyline:
        return segment.route_polyline

    if not can_make_directions_call():
        print("❌ Directions API quota exceeded for this month.")
        return None

    polyline = get_directions_polyline(
        segment.from_lat, segment.from_lng,
        segment.to_lat, segment.to_lng
    )
    if polyline:
        segment.route_polyline = polyline
        segment.save()
    return polyline