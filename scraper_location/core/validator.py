import os
import datetime
import json
import hashlib
import requests
from fuzzywuzzy import fuzz
from scraper_location.core.logger import log_validator_result
import Levenshtein
from scraper_location.config.constants import GOOD_TYPES

class LocationValidator:
    def __init__(self, jalan_file: str, cache_file: str, api_key: str, kota_file: str, api_limit: int = 100):
        self.jalan_set = self._load_jalan_set(jalan_file)
        self.kota_set = self._load_kota_set(kota_file)
        self.cache_file = cache_file
        self.api_key = api_key
        self.api_url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
        self.api_limit = api_limit
        self.api_counter = 0
        self.cache = self._load_cache(cache_file)
        self.debug = True

    def _load_jalan_set(self, abs_path: str) -> set:
        with open(abs_path, 'r', encoding='utf-8') as f:
            return set(item[0].lower() for item in json.load(f) if item)

    def _load_kota_set(self, abs_path: str) -> set:
        with open(abs_path, 'r', encoding='utf-8') as f:
            return set(entry.lower() for entry in json.load(f) if isinstance(entry, str))

    def _load_cache(self, abs_path: str) -> dict:
        if os.path.exists(abs_path):
            with open(abs_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _hash_key(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def is_within_surabaya_sidoarjo_bbox(self, lat, lng):
        """
        Check apakah koordinat di dalam box Surabaya + Sidoarjo.
        """
        # Contoh perkiraan box, bisa kamu refine:
        SURABAYA_SIDOARJO_BBOX = {
            "min_lat": -7.5,
            "max_lat": -7.2,
            "min_lng": 112.6,
            "max_lng": 112.8
        }

        return (SURABAYA_SIDOARJO_BBOX["min_lat"] <= lat <= SURABAYA_SIDOARJO_BBOX["max_lat"]) and \
            (SURABAYA_SIDOARJO_BBOX["min_lng"] <= lng <= SURABAYA_SIDOARJO_BBOX["max_lng"])
   
 
    def save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def is_location_name_too_general(self, loc_text) -> bool:
        """
        Cek apakah nama lokasi terlalu umum berdasarkan daftar kota Indonesia.
        Bisa menerima string atau dict dari cache.
        """
        if isinstance(loc_text, dict):
            loc_text = loc_text.get("original", "")

        if not isinstance(loc_text, str):
            return False

        normalized = loc_text.lower().strip()
        return normalized in self.kota_set
    
    def fuzzy_check_location(self, loc_text):
        loc = loc_text.lower().strip()
        loc_tokens = set(loc.split())

        for known in self.jalan_set:
            ratio = fuzz.token_set_ratio(loc, known)
            sort_ratio = fuzz.token_sort_ratio(loc, known)
            distance = Levenshtein.distance(loc, known)
            len_diff = abs(len(loc) - len(known))

            overlap = loc_tokens & set(known.split())

            if ratio >= 85 and sort_ratio >= 85:
                if (len_diff <= 5 or distance <= 5) and len(overlap) >= 1:
                    return known, True, f"Fuzzy+Edit OK input='{loc_text}', matched='{known}'(ratio={ratio}, sort={sort_ratio}, dist={distance}, overlap={overlap})"

        return loc_text, False, "No match by fuzzy+edit distance"
    
    def google_check_location(self, loc_text):
        loc = loc_text.lower().strip()
        key = self._hash_key(loc)
        cache_file = self.cache_file

        # Load cache jika ada
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                self.cache = json.load(f)

        if key in self.cache:
            cached = self.cache[key]
            return loc_text, cached.get("valid", False), "From cache"

        if not hasattr(self, "api_call_count"):
            self.api_call_count = 0
        if self.api_call_count >= 150:
            return loc_text, False, "API limit exceeded (max 150 calls)"

        params = {
            "input": loc,
            "inputtype": "textquery",
            "fields": "place_id,name,geometry,formatted_address,types",
            "region": "id",
            "key": self.api_key
        }

        try:
            res = requests.get(self.api_url, params=params).json()
            self.api_call_count += 1

            candidates = res.get("candidates", [])
            valid = False

            if candidates:
                c = candidates[0]
                addr = c.get("formatted_address", "").lower()
                types = c.get("types", [])

                # Filter lebih ketat: Surabaya atau Sidoarjo + optional types
                if ("surabaya" in addr or "sidoarjo" in addr):
                    good_types = GOOD_TYPES
                    if not good_types or any(t in types for t in good_types):
                        valid = True

                self.cache[key] = {
                    "input": loc,
                    "valid": valid,
                    "place_id": c.get("place_id"),
                    "name": c.get("name"),
                    "formatted_address": addr,
                    "types": types,
                    "lat": c["geometry"]["location"]["lat"],
                    "lng": c["geometry"]["location"]["lng"]
                }

                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=2)

                return loc_text, valid, f"From Google API (Valid: {valid}, addr: {addr})"

            else:
                self.cache[key] = {"valid": False}
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=2)
                return loc_text, False, "Not found in Google API"

        except Exception as e:
            return loc_text, False, f"Google API error: {str(e)}"
  
    def is_it_valid_location(self, loc_text):
        # 1️⃣ Fuzzy
        word, valid, reason = self.fuzzy_check_location(loc_text)
        log_validator_result(loc_text, word, valid, reason, method="fuzzy")

        if valid:
            return word, valid, reason

        # 2️⃣ Google API
        word, valid, reason = self.google_check_location(loc_text)
        log_validator_result(loc_text, word, valid, reason, method="google")

        return word, valid, reason

