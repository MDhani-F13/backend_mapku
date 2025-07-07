import json
from rule_engine import check_rules, check_rules_step1
from scraper_location.core.validator import LocationValidator
from scraper_location.config.config_loader import ConfigLoader
from scraper_location.core.logger import setup_logger

# === Konfigurasi
INPUT_FILE = "output/structured_tweets_v21.json"
OUTPUT_FILE_VALID = "output/rechecktest1.json"
OUTPUT_FILE_REJECTED = "output/rejecttest1.json"

JALAN_FILE = 'daftar_jalan_surabaya.json'
KOTA_FILE = 'daftar_kota_indonesia.json'
CACHE_FILE = 'google_location_cache.json'

def main():
    logger = setup_logger()
    config = ConfigLoader()
    api_key = config.get_google_api_key()
    validator = LocationValidator(JALAN_FILE, CACHE_FILE, api_key, KOTA_FILE)

    # Load tweet data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"[INFO] Loaded {len(data)} tweet entries from {INPUT_FILE}")

    rechecked_valid = []
    rejected_tweets = []

    for tweet in data:
        merged_tags = tweet.get("merged_tags", [])
        if not merged_tags:
            continue

        structured_info = check_rules_step1(merged_tags, tweet_obj=tweet)
        #structured_info = check_rules(merged_tags, validator, tweet_obj=tweet, debug=True)
        tweet["structured_info"] = structured_info

        if structured_info is None:
            rejected_tweets.append(tweet)
        else:
            rechecked_valid.append(tweet)

    # Simpan hasil valid
    with open(OUTPUT_FILE_VALID, 'w', encoding='utf-8') as f:
        json.dump(rechecked_valid, f, ensure_ascii=False, indent=4)

    # Simpan hasil ditolak
    with open(OUTPUT_FILE_REJECTED, 'w', encoding='utf-8') as f:
        json.dump(rejected_tweets, f, ensure_ascii=False, indent=4)

    # Print ringkasan
    total = len(data)
    rejected = len(rejected_tweets)
    accepted = total - rejected

    print(f"[SUMMARY] Total tweets        : {total}")
    print(f"[SUMMARY] ✅ Valid entries     : {accepted} (saved to {OUTPUT_FILE_VALID})")
    print(f"[SUMMARY] ❌ Rejected entries  : {rejected} (saved to {OUTPUT_FILE_REJECTED})")

    validator.save_cache()

if __name__ == "__main__":
    main()