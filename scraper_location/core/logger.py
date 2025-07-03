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