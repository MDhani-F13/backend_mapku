import tweepy
import random
import asyncio

class SimpleUser:
    def __init__(self, name):
        self.name = name

class SimpleTweet:
    def __init__(self, id, text, created_at, username="Unknown"):
        self.id = id
        self.text = text
        self.created_at = created_at
        self.user = SimpleUser(username)


class TwitterClient:
    def __init__(self, bearer_token, delay_range=(8, 18)):
        self.delay_range = delay_range
        self.client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
        print("🔗 Twitter Official API Client Ready")

    async def fetch_latest_tweets(self, query: str, limit: int = 12): 
        try:
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(limit, 12),
                tweet_fields=["created_at","author_id","text"]
            )

            if not response.data:
                print(f"⚠ No tweets found for {query}")
                return []

            # Cooldown untuk hemat kuota
            await asyncio.sleep(random.uniform(*self.delay_range))

            return [
                SimpleTweet(
                    id=t.id,
                    text=t.text,
                    created_at=t.created_at,
                    username=str(t.author_id)  
                )
                for t in response.data
            ]

        except Exception as e:
            print(f"❌ Twitter API Error: {e}")
            return []
