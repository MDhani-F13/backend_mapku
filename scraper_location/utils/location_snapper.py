import os
import re
import requests
from geopy.distance import geodesic

from scraper_location.utils.quota_tracker import QuotaTracker
from scraper_location.core.logger import log_snapper
from scraper_location.config.major_areas import MAJOR_AREAS

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
tracker = QuotaTracker()

def is_area(location_name: str) -> bool:
    """
    Area check dengan word boundary dan pengecualian prefix Jalan.
    """
    if not location_name:
        return False

    name_lower = location_name.lower().strip()

    # 1) Jika ada prefix 'jl.' atau 'jalan' ➜ langsung False
    if name_lower.startswith("jl") or name_lower.startswith("jalan"):
        return False

    # 2) Word boundary match ke daftar major area
    for _, levels in MAJOR_AREAS.items():
        for _, area_list in levels.items():
            for area in area_list:
                area_lower = area.lower().strip()
                if re.search(rf"\b{re.escape(area_lower)}\b", name_lower):
                    return True

    return False

def snap_to_major_road_multi(lat: float, lng: float) -> list:
    """
    Nearby Search ➜ beberapa kandidat simpang/exit/jalan utama.
    """
    if not tracker.can_use():
        print("[QuotaTracker] Limit Places API TERCAPAI.")
        return []

    places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 2000,
        "keyword": "simpang OR intersection OR exit",
        "key": GOOGLE_API_KEY
    }

    try:
        resp = requests.get(places_url, params=params)
        resp.raise_for_status()
        data = resp.json()

        if "results" in data and data["results"]:
            tracker.increment()
            candidates = []
            for item in data["results"]:
                loc = item["geometry"]["location"]
                candidates.append({
                    "name": item["name"],
                    "lat": loc["lat"],
                    "lng": loc["lng"]
                })
            return candidates

    except Exception as e:
        print(f"[snap_to_major_road_multi] Error: {e}")

    return []

def snap_location_pair(from_loc, to_loc, from_lat, from_lng, to_lat, to_lng):
    """
    Final smart snap:
    1) Luas ➜ Sempit ➜ snap sempit, replace luas.
    2) Sempit ➜ Luas ➜ snap sempit, replace luas.
    3) Luas ➜ Luas ➜ snap keduanya.
    4) Sempit ➜ Sempit ➜ biarkan.
    """
    new_from = {"location": from_loc, "lat": from_lat, "lng": from_lng, "reason": "original"}
    new_to = {"location": to_loc, "lat": to_lat, "lng": to_lng, "reason": "original"}

    from_is_area = is_area(from_loc)
    to_is_area = is_area(to_loc)

    print(f"[Snapper] from_is_area={from_is_area}, to_is_area={to_is_area}")

    # 1) Luas ➜ Sempit ➜ snap sempit, ganti luas
    if from_is_area and not to_is_area and to_lat and to_lng:
        candidates = snap_to_major_road_multi(to_lat, to_lng)
        if candidates:
            best = min(
                candidates,
                key=lambda c: geodesic((c["lat"], c["lng"]), (from_lat, from_lng)).meters
            )
            new_from.update({
                "location": best["name"],
                "lat": best["lat"],
                "lng": best["lng"],
                "reason": "snap_from_by_nearby_of_to"
            })
            log_snapper({
                "action": "snap_from",
                "original": from_loc,
                "new": best["name"],
                "used_lat": to_lat,
                "used_lng": to_lng
            })

    # 2) Sempit ➜ Luas ➜ snap sempit, ganti luas
    elif to_is_area and not from_is_area and from_lat and from_lng:
        candidates = snap_to_major_road_multi(from_lat, from_lng)
        if candidates:
            best = min(
                candidates,
                key=lambda c: geodesic((c["lat"], c["lng"]), (to_lat, to_lng)).meters
            )
            new_to.update({
                "location": best["name"],
                "lat": best["lat"],
                "lng": best["lng"],
                "reason": "snap_to_by_nearby_of_from"
            })
            log_snapper({
                "action": "snap_to",
                "original": to_loc,
                "new": best["name"],
                "used_lat": from_lat,
                "used_lng": from_lng
            })

    # 3) Luas ➜ Luas ➜ snap keduanya
    elif from_is_area and to_is_area:
        if from_lat and from_lng:
            from_candidates = snap_to_major_road_multi(from_lat, from_lng)
            if from_candidates:
                best_from = from_candidates[0]
                new_from.update({
                    "location": best_from["name"],
                    "lat": best_from["lat"],
                    "lng": best_from["lng"],
                    "reason": "snap_from_both_area"
                })
                log_snapper({
                    "action": "snap_from_both",
                    "original": from_loc,
                    "new": best_from["name"]
                })
        if to_lat and to_lng:
            to_candidates = snap_to_major_road_multi(to_lat, to_lng)
            if to_candidates:
                best_to = to_candidates[0]
                new_to.update({
                    "location": best_to["name"],
                    "lat": best_to["lat"],
                    "lng": best_to["lng"],
                    "reason": "snap_to_both_area"
                })
                log_snapper({
                    "action": "snap_to_both",
                    "original": to_loc,
                    "new": best_to["name"]
                })

    # 4) Sempit ➜ Sempit ➜ biarkan

    return new_from, new_to
