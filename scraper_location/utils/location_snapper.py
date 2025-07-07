import os
import requests
from scraper_location.utils.quota_tracker import QuotaTracker
from scraper_location.core.logger import log_snapper
from scraper_location.config.major_areas import MAJOR_AREAS

import os
import requests
from scraper_location.utils.quota_tracker import QuotaTracker
from scraper_location.core.logger import log_snapper
from scraper_location.config.major_areas import MAJOR_AREAS

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
tracker = QuotaTracker()

def is_area(location_name: str) -> bool:
    if not location_name:
        return False
    loc_lower = location_name.lower()
    for _, levels in MAJOR_AREAS.items():
        for _, area_list in levels.items():
            for area in area_list:
                if area.lower() in loc_lower:
                    return True
    return False

def snap_to_major_road(location_name: str, lat: float, lng: float) -> dict:
    if not tracker.can_use():
        print("[QuotaTracker] Limit Places API TERCAPAI. Fallback to original.")
        result = {
            "location": location_name,
            "lat": lat,
            "lng": lng,
            "reason": "limit_exceeded"
        }
        log_snapper(result)
        return result

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
            first_result = data["results"][0]
            name = first_result["name"]
            loc = first_result["geometry"]["location"]

            tracker.increment()

            result = {
                "location": name,
                "lat": loc["lat"],
                "lng": loc["lng"],
                "reason": "google_places_snap"
            }
            log_snapper(result)
            return result

    except Exception as e:
        print(f"[snap_to_major_road] Error: {e}")

    result = {
        "location": location_name,
        "lat": lat,
        "lng": lng,
        "reason": "api_error_or_empty"
    }
    log_snapper(result)
    return result

def snap_location_pair(from_loc, to_loc, from_lat, from_lng, to_lat, to_lng):
    new_from = {"location": from_loc, "lat": from_lat, "lng": from_lng, "reason": "original"}
    new_to = {"location": to_loc, "lat": to_lat, "lng": to_lng, "reason": "original"}

    from_is_area = is_area(from_loc)
    to_is_area = is_area(to_loc)

    if from_is_area and not to_is_area and to_lat and to_lng:
        snapped = snap_to_major_road(from_loc, to_lat, to_lng)
        new_from.update(snapped)

    elif to_is_area and not from_is_area and from_lat and from_lng:
        snapped = snap_to_major_road(to_loc, from_lat, from_lng)
        new_to.update(snapped)

    elif from_is_area and to_is_area:
        if from_lat and from_lng:
            snapped_from = snap_to_major_road(from_loc, from_lat, from_lng)
            new_from.update(snapped_from)
        if to_lat and to_lng:
            snapped_to = snap_to_major_road(to_loc, to_lat, to_lng)
            new_to.update(snapped_to)

    return new_from, new_to

