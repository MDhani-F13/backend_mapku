import os
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self, path='.env'):
        load_dotenv(path)

    def get_twitter_credentials(self):
        return {
            "username": os.getenv('TWITTER_USERNAME'),
            "email": os.getenv('TWITTER_EMAIL'),
            "password": os.getenv('TWITTER_PASSWORD'),
            "totp_secret": os.getenv("TOTP_SECRET")
        }

    def get_google_api_key(self):
        return os.getenv('GOOGLE_API_KEY')
