import os
import asyncio
import json
from datetime import datetime
from scraper_location.utils.text_cleaner import clean_tweet, is_relevant
from scraper_location.utils.merger import merge_pos_ner


class TweetScraper:
    def __init__(
        self,
        twitter_client,
        validator,
        nlp_pipeline,
        queries: list,
        output_file: str,
        unstructured_file: str,
        debug: bool = False
    ):
        self.twitter_client = twitter_client
        self.validator = validator
        self.nlp = nlp_pipeline
        self.queries = queries
        self.output_file = output_file
        self.unstructured_file = unstructured_file
        self.collected_tweet_ids = set()
        self.structured_tweets = []
        self.debug = debug

    async def scrape(self, return_data=True):
        for idx, query in enumerate(self.queries):
            print(f"📥 Fetching tweets for: {query}")

            try:
                tweets = await self.twitter_client.fetch_latest_tweets(query)
            except Exception as e:
                print(f"❌ Error query '{query}': {e}")
                continue

            for tweet in tweets:
                if tweet.id in self.collected_tweet_ids:
                    continue
                self.collected_tweet_ids.add(tweet.id)
                self.process_tweet(tweet, query)
                 
            if idx < len(self.queries)-1:
                print("⏳ Menunggu 16 menit sebelum query berikutnya...")
                await asyncio.sleep(60 * 16)  # ← 16 menit aman

        if self.output_file:
            self.save_results()

        return self.structured_tweets

    def save_results(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.structured_tweets, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved structured tweets to {self.output_file}")

    def process_tweet(self, tweet, query):
        cleaned = clean_tweet(tweet.text)
        if not is_relevant(cleaned):
            return

        ner = self.nlp.extract_ner(cleaned)
        pos = self.nlp.extract_pos(cleaned)
        merged = merge_pos_ner(pos, ner)

        self.structured_tweets.append({
            "tweet_id": tweet.id,
            "query": query,
            "user": tweet.user.name,
            "text": tweet.text,
            "cleaned_text": cleaned,
            "created_at": tweet.created_at.isoformat(),
            "ner_entities": ner,
            "pos_tags": pos,
            "merged_tags": merged
        })

        if self.debug:
            with open("debug_last_tweet.json","w",encoding='utf-8') as f:
                json.dump(self.structured_tweets[-1],f,indent=4,ensure_ascii=False)
