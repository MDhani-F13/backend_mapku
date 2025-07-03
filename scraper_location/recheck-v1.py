import json
import os
from rule_engine import check_rules_step1 , check_rules_step2, check_rules_step3
from core.logger import setup_logger
from config.config_loader import ConfigLoader
from core.validator import LocationValidator

INPUT_FILE = "output/structured_tweets_v21.json"
OUTPUT_FILE = "output/rechecked_step3-iteration2.json"
JALAN_FILE = 'daftar_jalan_surabaya.json'
KOTA_FILE = 'daftar_kota_indonesia.json'
CACHE_FILE = 'google_location_caches.json'

def main():
    logger = setup_logger()
    config = ConfigLoader()  
    api_key = config.get_google_api_key()
    validator = LocationValidator(JALAN_FILE, CACHE_FILE, api_key, KOTA_FILE)
    rechecked = []
    rejected = []

    # Pastikan output folder ada
    os.makedirs("output", exist_ok=True)

    # Baca data
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[INFO] Loaded {len(data)} tweets from {INPUT_FILE}")

    for tweet in data:
        merged_tags = tweet.get("merged_tags", [])
        if not merged_tags:
            continue

        #Jalankan STEP 1 dan 2
        result_step1 = check_rules_step1(merged_tags, validator, tweet_obj=tweet)
        result_step2 = check_rules_step2(result_step1)
        result_step3 = check_rules_step3(result_step2, validator)

        # Step 1 tidak reject → selalu masuk rechecked
        tweet["step1_info"] = result_step1
        tweet["step2_info"] = result_step2
        tweet["step3_info"] = result_step3
        rechecked.append(tweet)

    # Simpan hasil
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rechecked, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Rechecked saved to {OUTPUT_FILE}")
    print(f"[INFO] Step 1 log: logs/check_rules_step1.jsonl")

if __name__ == "__main__":
    main()