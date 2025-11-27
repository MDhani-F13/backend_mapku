import json, os
import random
import asyncio
from scraper_location.config.config_loader import ConfigLoader
from scraper_location.core.logger import setup_logger
from scraper_location.core.validator import LocationValidator
from scraper_location.core.nlp_pipeline import NLPPipeline
from scraper_location.core.twitter_client import TwitterClient
from scraper_location.scraper import TweetScraper
from scraper_location.rule_engine import check_rules_step1, check_rules_step2, check_rules_step3
from scraper_location.db_writer import save_pipeline_results_to_db

# Konstanta
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALL_QUERIES = [
    "from:e100ss (penutupan OR pengalihan OR rekayasa) jalan surabaya -arisan -pkk -pengajian -event -acara",
    "from:e100ss (jalan AND (ditutup OR dialihkan OR rekayasa)) surabaya -acara -hoax -nasional -luar",
    "from:e100ss (akses OR ruas) AND (ditutup OR tidak bisa dilewati) surabaya -rapat -acara",
    "from:e100ss kemacetan OR padat OR tersendat surabaya -arisan -event -info"
]


async def run_pipeline(config_path="config.ini", output_file=None, queries=None, tweet_file=None):
    """
    Jalankan scraping + preprocessing step 1~3
    Return: list of hasil tweet
    """
    logger = setup_logger()
    config = ConfigLoader(config_path)
    credentials = config.get_twitter_credentials()
    api_key = config.get_google_api_key()

    # File konfigurasi
    #cookie_file = 'cookies.json'
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    jalan_file = os.path.join(BASE_PATH, 'daftar_jalan_surabaya.json')
    kota_file = os.path.join(BASE_PATH,'daftar_kota_indonesia.json')
    cache_file = os.path.join(BASE_PATH, 'google_location_caches.json')

    if tweet_file is None:
        tweet_file = os.path.join(OUTPUT_DIR, 'tweet_final.json')

    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'preprocess_step1-3_final.json')

    if queries is None:
        queries = random.sample(ALL_QUERIES, 4)

    # Inisialisasi
    validator = LocationValidator(jalan_file, cache_file, api_key, kota_file)
    nlp = NLPPipeline()
    twitter = TwitterClient(
        bearer_token=credentials["bearer_token"],  
        delay_range=(8, 18)
    )

    scraper = TweetScraper(
        twitter_client=twitter,
        validator=validator,
        nlp_pipeline=nlp,
        queries=queries,
        output_file=tweet_file,
        unstructured_file=None,
        debug=True
    )

    tweets = await scraper.scrape(return_data=True)

    print(f"[INFO] ✅ Scraped {len(tweets)} tweets")

    # Langkah B: Jalankan Step 1 ~ Step 3
    final_data = []
    for tweet in tweets:
        merged_tags = tweet.get("merged_tags", [])
        if not merged_tags:
            continue

        result_step1 = check_rules_step1(merged_tags, validator, tweet_obj=tweet)
        result_step2 = check_rules_step2(result_step1)
        result_step3 = check_rules_step3(result_step2, validator)

        tweet["step1_info"] = result_step1
        tweet["step2_info"] = result_step2
        tweet["step3_info"] = await result_step3

        final_data.append(tweet)

    # Simpan (jika diinginkan)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 🔄 Final result saved to {output_file}")

        await save_pipeline_results_to_db(output_file)
    return final_data


# Jika file dijalankan langsung
if __name__ == "__main__":
    asyncio.run(run_pipeline())
