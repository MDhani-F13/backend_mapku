import asyncio
import random
from twikit import Client, errors
import os

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
]

class TwitterClient:
    def __init__(self, locale='en-US', delay_range=(10, 20), relogin_delay_range=(5, 15), max_relogin_attempts=3):
        self.client = Client(locale)
        self.logged_in = False
        self._rotate_user_agent()
        self.username = None
        self.email = None
        self.password = None
        self.cookie_file = None
        self.totp_secret = None
        self.delay_range = delay_range
        self.relogin_delay_range = relogin_delay_range
        self.max_relogin_attempts = max_relogin_attempts

    def _rotate_user_agent(self):
        self.client.http.headers.update({
            "User-Agent": random.choice(USER_AGENTS)
        })

    def load_cookies(self, cookie_file: str):
        try:
            self.client.load_cookies(cookie_file)
            self.logged_in = self._is_cookie_valid()
            if self.logged_in:
                print("✅ Cookies loaded and validated.")
            else:
                print("⚠️ Cookies invalid, login required.")
        except Exception as e:
            print(f"⚠️ Failed to load cookies: {e}")
            self.logged_in = False

    def _is_cookie_valid(self) -> bool:
        try:
            user = self.client.get_me()
            return user is not None
        except Exception:
            return False

    async def login(self, username: str, email: str, password: str, cookie_file: str, totp_secret=None):
        self.username = username
        self.email = email
        self.password = password
        self.cookie_file = cookie_file
        self.totp_secret = totp_secret

        if os.path.exists(cookie_file):
            self.load_cookies(cookie_file)
            if self.logged_in:
                return

        self._rotate_user_agent()

        try:
            print("Attempting login...")
            await self.client.login(
                auth_info_1=username,
                auth_info_2=email,
                password=password,
                totp_secret=totp_secret
            )
            self.client.save_cookies(cookie_file)
            self.logged_in = True
            print(" Logged in and cookies saved.")
        except errors.TwitterException as e:
            print(f" Login failed: {e}")
            raise

    async def _auto_relogin(self):
        for attempt in range(1, self.max_relogin_attempts + 1):
            wait_time = random.uniform(*self.relogin_delay_range)
            print(f"🔁 Re-attempting login (Attempt {attempt}/{self.max_relogin_attempts}) in {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)

            try:
                await self.login(
                    self.username,
                    self.email,
                    self.password,
                    self.cookie_file,
                    self.totp_secret
                )
                if self.logged_in:
                    print(f" Re-login successful on attempt {attempt}")
                    return
            except Exception as e:
                print(f" Re-login attempt {attempt} failed: {e}")

        print(f" All {self.max_relogin_attempts} relogin attempts failed.")

    async def fetch_latest_tweets(self, query: str, limit: int = 15):
        try:
            if not self.logged_in:
                raise errors.Unauthorized("Not logged in")

            tweets = await self.client.search_tweet(query, 'Latest')
            wait_time = random.uniform(*self.delay_range)
            print(f" Delay {wait_time:.2f} seconds after query.")
            await asyncio.sleep(wait_time)
            return tweets[:limit]

        except errors.Unauthorized:
            print(" Unauthorized: trying to re-login and retry fetch.")
            await self._auto_relogin()
            if not self.logged_in:
                print(" Cannot fetch tweets: re-login failed.")
                return []
            try:
                tweets = await self.client.search_tweet(query, 'Latest')
                return tweets[:limit]
            except Exception as e:
                print(f" Retried fetch failed: {e}")
                return []

        except Exception as e:
            print(f" Error fetching tweets: {e}")
            return []
