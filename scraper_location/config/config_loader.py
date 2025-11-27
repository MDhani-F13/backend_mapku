import os
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self, path='.env'):
        load_dotenv(path)

    def get_twitter_credentials(self):
        return {
            "bearer_token": os.getenv('BEARER_TOKEN'),
        }

    def get_google_api_key(self):
        return os.getenv('GOOGLE_API_KEY')
