import os
import json
from datetime import datetime

class QuotaTracker:
    def __init__(self, quota_file="logs/places_quota.json", monthly_limit=5000, daily_limit=200):
        self.quota_file = quota_file
        self.monthly_limit = monthly_limit
        self.daily_limit = daily_limit

        # Init file kalau belum ada
        if not os.path.exists(self.quota_file):
            self._reset_quota()

        # Load
        with open(self.quota_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def _reset_quota(self):
        now = datetime.utcnow()
        self.data = {
            "month": now.strftime("%Y-%m"),
            "daily": {},
            "monthly_count": 0
        }
        self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
        with open(self.quota_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def _today_key(self):
        now = datetime.utcnow()
        return now.strftime("%Y-%m-%d")

    def increment(self):
        now = datetime.utcnow()
        current_month = now.strftime("%Y-%m")
        today = self._today_key()

        # Reset kalau bulan ganti
        if self.data["month"] != current_month:
            self._reset_quota()
            self.data["month"] = current_month

        self.data["monthly_count"] += 1
        self.data["daily"][today] = self.data["daily"].get(today, 0) + 1

        self._save()

    def can_use(self):
        now = datetime.utcnow()
        current_month = now.strftime("%Y-%m")
        today = self._today_key()

        # Reset kalau bulan ganti
        if self.data["month"] != current_month:
            self._reset_quota()
            self.data["month"] = current_month

        if self.data["monthly_count"] >= self.monthly_limit:
            return False

        daily_count = self.data["daily"].get(today, 0)
        if daily_count >= self.daily_limit:
            return False

        return True

    def status(self):
        today = self._today_key()
        daily = self.data["daily"].get(today, 0)
        return {
            "monthly_count": self.data["monthly_count"],
            "daily_count": daily
        }
