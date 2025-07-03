import re
import logging
from scraper_location.config.constants import WHITELIST_ACTIONS, BLACKLIST_WORDS, TRAFFIC_SUFFIXES, DIRECTION_WORDS

MAX_LENGTH_WORDS = 60

def clean_tweet(tweet: str) -> str:
    """Bersihkan tweet dari link, mention, hashtag, dan spasi berlebih."""
    tweet = re.sub(r'http\S+|www\S+', '', tweet)
    tweet = re.sub(r'@\w+', '', tweet)
    tweet = re.sub(r'#\w+', '', tweet)
    tweet = re.sub(r'\s+', ' ', tweet)
    tweet = re.sub(r"\b[Pp]endengar\s+SS(-[A-Z]+)?\b", "", tweet)
    tweet = re.sub(r"\bSS(-[A-Z]+)?\b", "", tweet)
    return tweet.strip()

def is_relevant(text: str) -> bool:
    """Tentukan apakah tweet relevan berdasarkan panjang dan whitelist kata aksi."""
    text = text.lower().strip()

    if len(text.split()) > MAX_LENGTH_WORDS:
        logging.info(f"Rejected (Too long): {text}")
        return False

    if any(black in text for black in BLACKLIST_WORDS):
        logging.info(f"Rejected (Blacklisted): {text}")
        return False

    tokens = set(text.split())
    for action in WHITELIST_ACTIONS:
        for token in tokens:
            if _fuzzy_match(action, token):
                logging.info(f"Accepted (Matched action '{action}' with token '{token}'): {text}")
                return True

    logging.info(f"Rejected (No matching action): {text}")
    return False

def _fuzzy_match(a: str, b: str) -> bool:
    """Match sederhana untuk whitelist: cocok sebagian (tanpa fuzzywuzzy untuk efisiensi)."""
    return a in b or b in a

def clean_traffic_words(word: str) -> str:
    tokens = word.strip().split()

    # Hapus suffix kalau match
    if tokens and tokens[-1].lower() in TRAFFIC_SUFFIXES:
        tokens = tokens[:-1]

    # Hapus prefix kalau match
    if tokens and tokens[0].lower() in TRAFFIC_SUFFIXES:
        tokens = tokens[1:]

    return ' '.join(tokens)

def clean_direction_words(word: str) -> str:
    tokens = word.strip().split()

    # Hapus suffix 'arah'
    if tokens and tokens[-1].lower() in DIRECTION_WORDS:
        tokens = tokens[:-1]

    # Hapus prefix 'arah'
    if tokens and tokens[0].lower() in DIRECTION_WORDS:
        tokens = tokens[1:]

    return ' '.join(tokens)

def clean_and_split(word: str):
    """
    Pisahkan prefix/suffix traffic & direction.
    Return:
        - base: string
        - extras: [(token, tag)]
    """
    tokens = word.strip().split()
    extras = []

    # Suffix traffic
    if tokens and tokens[-1].lower() in TRAFFIC_SUFFIXES:
        suffix = tokens.pop(-1)
        extras.append((suffix, "VERB"))

    # Prefix/suffix direction word
    if tokens and tokens[0].lower() in DIRECTION_WORDS:
        prefix = tokens.pop(0)
        extras.append((prefix, "ADP"))
    if tokens and tokens[-1].lower() in DIRECTION_WORDS:
        suffix = tokens.pop(-1)
        extras.append((suffix, "ADP"))

    base = ' '.join(tokens)
    return base, extras
