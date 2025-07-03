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
        self.unstructured_tweets = []
        self.debug = debug

    async def scrape(self, username, email, password, cookie_file, return_data=False, totp_secret=None):
        if os.path.exists(cookie_file):
            self.twitter_client.load_cookies(cookie_file)
        if not self.twitter_client.logged_in:
            await self.twitter_client.login(username, email, password, cookie_file, totp_secret)

        for query in self.queries:
            print(f"📥 Fetching tweets for query: {query}")
            try:
                tweets = await self.twitter_client.fetch_latest_tweets(query)
            except Exception as e:
                print(f"❌ Error in query: {e}")
                continue

            for tweet in tweets:
                if tweet.id in self.collected_tweet_ids:
                    continue
                self.collected_tweet_ids.add(tweet.id)
                self.process_tweet(tweet, query)

        if self.output_file:
            self.save_results()

        if return_data:
            return self.structured_tweets

    def save_results(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.structured_tweets, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved structured tweets to {self.output_file}")

    def process_tweet(self, tweet, query):
        text = tweet.text
        cleaned = clean_tweet(text)

        if not is_relevant(cleaned):
            return

        ner_entities = self.nlp.extract_ner(cleaned)
        pos_tags = self.nlp.extract_pos(cleaned)
        merged_tags = merge_pos_ner(pos_tags, ner_entities)

        tweet_data = {
            "tweet_id": tweet.id, 
            "query": query,
            "user": tweet.user.name,
            "text": text,
            "cleaned_text": cleaned,
            "created_at": tweet.created_at.format(),
            "ner_entities": ner_entities,
            "pos_tags": pos_tags,
            "merged_tags": merged_tags
        }

        self.structured_tweets.append(tweet_data)

        if self.debug:
            with open("debug_last_tweet.json", 'w', encoding='utf-8') as f:
                json.dump(tweet_data, f, ensure_ascii=False, indent=4)
