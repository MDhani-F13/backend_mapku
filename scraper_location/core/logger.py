import datetime
import json
import logging
import os

def setup_logger(filename='logs/rejection_log.txt'):
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename=filename,
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        encoding='utf-8'
    )
    return logging.getLogger("location_rejection")

def log_validator_result(original, checked_word, valid, reason, method):
    """
    Logging hasil validasi lokasi ke logs/validator_result.jsonl
    """
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/validator_result.jsonl"

    log_entry = {
        "original": original,
        "checked_word": checked_word,
        "valid": valid,
        "reason": reason,
        "method": method,
        "timestamp": datetime.datetime.now().isoformat()
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def log_merge_adjacent_result(buffer, combined_valid, parts_valid):
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/merger_merge_adjacent_locations.jsonl"
    entry = {
        "buffer": buffer,
        "combined_valid": combined_valid,
        "parts_valid": parts_valid,
        "timestamp": datetime.datetime.now().isoformat()
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_promote_jalan_result(word, promoted, valid):
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/tagutils_promote_jalan_tokens.jsonl"
    entry = {
        "word": word,
        "promoted": promoted,
        "valid": valid,
        "timestamp": datetime.datetime.now().isoformat()
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def log_promote_propn_result(word, original_tag, valid, reason, context_hit, result_tag):
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/tagutils_promote_propn.jsonl"

    entry = {
        "word": word,
        "original_tag": original_tag,
        "valid": valid,
        "reason": reason,
        "context_hit": context_hit,
        "result_tag": result_tag,
        "timestamp": datetime.datetime.now().isoformat()
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def log_promote_noun_result(word, result_tag,reason, valid):
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/tagutils_promote_noun.jsonl"
    entry = {
        "word": word,
        "result_tag": result_tag,
        "valid": valid,
        "reason": reason,
        "timestamp": datetime.datetime.now().isoformat()
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def log_step2_from_to(sentence, locs, from_loc, to_loc, reason):
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/step2_from_to.jsonl"
    entry = {
        "sentence": sentence,
        "locations": locs,
        "from": from_loc,
        "to": to_loc,
        "reason": reason,
        "timestamp": datetime.datetime.now().isoformat()
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def log_step3_enrich_result(entry):
    """
    Logging hasil enrich lat/lng di Step 3
    """
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/step3_enrich.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def log_snapper(data):
    log = {
        "timestamp": datetime.datetime.now().isoformat(),
        "data": data
    }
    print(json.dumps(log, indent=2))


def log_pair_sanity(data: dict):
    os.makedirs("logs", exist_ok=True)
    log_data = {
        "initial_from_location": data.get("from_loc_before"),
        "initial_to_location": data.get("to_loc_before"),
        "from_loc_after": data.get("from_loc_after"),
        "to_loc_after": data.get("to_loc_after"),
        "from_lat_before": data.get("from_lat_before"),
        "from_lng_before": data.get("from_lng_before"),
        "to_lat_before": data.get("to_lat_before"),
        "to_lng_before": data.get("to_lng_before"),
        "from_lat_after": data.get("from_lat_after"),
        "from_lng_after": data.get("from_lng_after"),
        "to_lat_after": data.get("to_lat_after"),
        "to_lng_after": data.get("to_lng_after"),
        "initial_distance_km": data.get("initial_distance_km"),
        "final_distance_km": data.get("latest_distance_km"),
        "timestamp": datetime.datetime.now().isoformat()
    }

    log_path = "logs/pair_sanity.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")

def log_sanity_filter_reject(tweet_id, tweet_text, debug_info):
    """
    Log tweet yang gagal filter anchor-directional.
    """
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/sanity_filter_rejected.jsonl"

    entry = {
        "tweet_id": tweet_id,
        "text": tweet_text,
        "debug_info": debug_info,
        "timestamp": datetime.datetime.now().isoformat()
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def log_snapper_candidates(data: dict):
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/snapper_candidates.jsonl"
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "data": data
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")