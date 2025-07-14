import os
import json
import re
import requests
from geopy.distance import geodesic
from geopy import Point
from geopy.distance import distance as geopy_distance

from scraper_location.utils.quota_tracker import QuotaTracker
from scraper_location.core.logger import log_snapper, log_snapper_candidates
from scraper_location.config.major_areas import MAJOR_AREAS
from scraper_location.utils.bearing_calc import bearing, bearing_diff

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
tracker = QuotaTracker()

EXCLUDED_PREFIXES = [
    "jl", "jalan", "bundaran", "terminal", "simpang",
    "halte", "exit", "gerbang", "pintu tol", "pos polisi", "pasar", "desa"
]

OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
GOOGLE_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_PATH, 'overpass_cache.json')


def load_overpass_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_overpass_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


overpass_cache = load_overpass_cache()


def cache_key(lat: float, lng: float, radius: int) -> str:
    return f"{round(lat, 5)}_{round(lng, 5)}_{radius}"


def is_area(location_name: str) -> bool:
    if not location_name:
        return False

    loc_lower = location_name.lower().strip()

    for prefix in EXCLUDED_PREFIXES:
        if loc_lower.startswith(prefix):
            return False

    for city in MAJOR_AREAS.get("kota", []):
        if loc_lower == city.lower():
            return True

    for _, levels in MAJOR_AREAS.items():
        if isinstance(levels, dict):
            for _, area_list in levels.items():
                for area in area_list:
                    if loc_lower == area.lower().strip():
                        return True

    return False


def _is_same_name(a: str, b: str) -> bool:
    def clean(s):
        s = s.lower().strip()
        s = re.sub(r'\b(jl|jalan|jalan raya|jalan besar|jalan tol|tol)\b', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    return clean(a) == clean(b)


def move_point(lat, lng, bearing_deg, offset_m):
    origin = Point(lat, lng)
    destination = geopy_distance(meters=offset_m).destination(origin, bearing_deg)
    return destination.latitude, destination.longitude


def overpass_snap_multi(lat: float, lng: float, input_name: str, target_lat: float, target_lng: float) -> dict | None:
    for radius in [500, 1000, 1500, 2000, 2500, 3000, 3500]:
        key = cache_key(lat, lng, radius)
        if key in overpass_cache:
            cached = overpass_cache[key]
            if cached is not None:
                if isinstance(cached, list):
                    if cached:
                        cached = cached[0]
                    else:
                        continue

                if _is_same_name(cached["name"], input_name):
                    continue

                diff = bearing_diff(lat, lng, target_lat, target_lng, cached["lat"], cached["lng"])
                if diff > 90:
                    continue

                return cached

        bearing_val = bearing(lat, lng, target_lat, target_lng)
        center_lat, center_lng = move_point(lat, lng, bearing_val, radius * 0.5)

        query = f"""
        [out:json];
        way["highway"](around:{radius},{center_lat},{center_lng});
        out tags center;
        """

        try:
            resp = requests.post(OVERPASS_API_URL, data={"data": query}, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            dist_sempit_target = geodesic((lat, lng), (target_lat, target_lng)).meters

            candidates = []
            for element in data.get("elements", []):
                name = element["tags"].get("name")
                center = element.get("center")
                if name and center:
                    dist_to_origin = geodesic((lat, lng), (center["lat"], center["lon"])).meters
                    dist_to_target = geodesic((target_lat, target_lng), (center["lat"], center["lon"])).meters

                    if _is_same_name(name, input_name):
                        continue
                    if dist_to_origin < 50:
                        continue

                    diff = bearing_diff(lat, lng, target_lat, target_lng, center["lat"], center["lon"])
                    if diff > 90:
                        continue

                    candidates.append({
                        "name": name,
                        "lat": center["lat"],
                        "lng": center["lon"],
                        "dist_to_origin": round(dist_to_origin, 2),
                        "dist_to_target": round(dist_to_target, 2),
                        "bearing_diff": round(diff, 2)
                    })

            if candidates:
                best = min(candidates, key=lambda c: c["dist_to_target"])

                log_snapper_candidates({
                    "sentence": f"Snap: {input_name}",
                    "direction": f"{lat},{lng} ➜ {target_lat},{target_lng}",
                    "bearing": round(bearing_val, 2),
                    "radius": radius,
                    "sempit_target_distance": round(dist_sempit_target, 2),
                    "candidates": candidates,
                    "chosen": best
                })

                overpass_cache[key] = best
                save_overpass_cache(overpass_cache)
                return best

        except Exception as e:
            print(f"[Overpass Snap] Error: {e}")

        overpass_cache[key] = None
        save_overpass_cache(overpass_cache)

    return None


def direction_snap(origin_lat, origin_lng, dest_lat, dest_lng) -> dict | None:
    if not tracker.can_use():
        return None

    params = {
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
        "key": GOOGLE_API_KEY
    }

    try:
        resp = requests.get(GOOGLE_DIRECTIONS_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        tracker.increment()

        routes = data.get("routes")
        if routes:
            steps = routes[0]["legs"][0]["steps"]
            if steps:
                first_step = steps[0]
                instruction = first_step.get("html_instructions", "")
                name = _extract_road_name(instruction)
                loc = first_step["start_location"]
                if name:
                    return {
                        "name": name,
                        "lat": loc["lat"],
                        "lng": loc["lng"]
                    }
    except Exception as e:
        print(f"[Direction Snap] Error: {e}")
    return None


def _extract_road_name(instruction: str) -> str | None:
    matches = re.findall(r'<b>(.*?)</b>', instruction)
    return matches[0] if matches else None


def snap_location_pair(from_loc, to_loc, from_lat, from_lng, to_lat, to_lng):
    new_from = {"location": from_loc, "lat": from_lat, "lng": from_lng, "reason": "original"}
    new_to = {"location": to_loc, "lat": to_lat, "lng": to_lng, "reason": "original"}

    from_is_area = is_area(from_loc)
    to_is_area = is_area(to_loc)

    print(f"[Snapper] from_is_area={from_is_area}, to_is_area={to_is_area}")

    if from_is_area and not to_is_area and to_lat and to_lng:
        result = overpass_snap_multi(to_lat, to_lng, to_loc, from_lat, from_lng) or \
                 direction_snap(to_lat, to_lng, from_lat, from_lng)
        if result:
            new_from.update({
                "location": result["name"],
                "lat": result["lat"],
                "lng": result["lng"],
                "reason": "snap_from_overpass_or_direction"
            })
            log_snapper({
                "action": "snap_from",
                "original": from_loc,
                "new": result["name"],
                "source": result
            })

    elif to_is_area and not from_is_area and from_lat and from_lng:
        result = overpass_snap_multi(from_lat, from_lng, from_loc, to_lat, to_lng) or \
                 direction_snap(from_lat, from_lng, to_lat, to_lng)
        if result:
            new_to.update({
                "location": result["name"],
                "lat": result["lat"],
                "lng": result["lng"],
                "reason": "snap_to_overpass_or_direction"
            })
            log_snapper({
                "action": "snap_to",
                "original": to_loc,
                "new": result["name"],
                "source": result
            })

    elif from_is_area and to_is_area:
        if from_lat and from_lng:
            result_from = overpass_snap_multi(from_lat, from_lng, from_loc, to_lat, to_lng) or \
                          direction_snap(from_lat, from_lng, to_lat, to_lng)
            if result_from:
                new_from.update({
                    "location": result_from["name"],
                    "lat": result_from["lat"],
                    "lng": result_from["lng"],
                    "reason": "snap_from_luas_luas"
                })
                log_snapper({
                    "action": "snap_from_luas_luas",
                    "original": from_loc,
                    "new": result_from["name"],
                    "source": result_from
                })

                result_to = overpass_snap_multi(
                    result_from["lat"],
                    result_from["lng"],
                    to_loc,
                    to_lat,
                    to_lng
                ) or direction_snap(
                    result_from["lat"],
                    result_from["lng"],
                    to_lat,
                    to_lng
                )

                if result_to:
                    new_to.update({
                        "location": result_to["name"],
                        "lat": result_to["lat"],
                        "lng": result_to["lng"],
                        "reason": "snap_to_luas_luas"
                    })
                    log_snapper({
                        "action": "snap_to_luas_luas",
                        "original": to_loc,
                        "new": result_to["name"],
                        "source": result_to
                    })

    return new_from, new_to
