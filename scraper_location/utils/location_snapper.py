import os
import re
import json
import requests
from geopy.distance import geodesic
from geopy import Point
from geopy.distance import distance as geopy_distance

from scraper_location.utils.quota_tracker import QuotaTracker
from scraper_location.core.logger import log_snapper_nominatim, log_snapper_overpass, log_snap_location_pair
from scraper_location.config.major_areas import MAJOR_AREAS
from scraper_location.utils.bearing_calc import bearing, bearing_diff
from scraper_location.utils.google_client import get_directions_polyline
from scraper_location.utils.polyline_utils import is_snap_near_polyline
from scraper_location.utils.polyline_cache import get_polyline, save_polyline

tracker = QuotaTracker()

EXCLUDED_PREFIXES = [
    "jl", "jalan", "bundaran", "terminal", "simpang",
    "halte", "exit", "gerbang", "pintu tol", "pos polisi", "pasar", "desa"
]

OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


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


def get_trayek_polyline(lat1, lng1, lat2, lng2):
    """
    Coba ambil polyline dari cache ➜ kalau miss, panggil Directions API ➜ simpan ke cache.
    """
    polyline = get_polyline(
        "polyline_cache.json",
        from_lat=lat1, from_lng=lng1,
        to_lat=lat2, to_lng=lng2
    )

    if polyline:
        return polyline

    # Miss ➜ fallback ke Directions Google
    polyline = get_directions_polyline(lat1, lng1, lat2, lng2)
    if polyline:
        save_polyline(
            "polyline_cache.json",
            from_lat=lat1, from_lng=lng1,
            to_lat=lat2, to_lng=lng2,
            polyline=polyline
        )

    return polyline


def overpass_snap_multi(lat: float, lng: float, input_name: str, target_lat: float, target_lng: float) -> dict | None:
    trayek_polyline = get_trayek_polyline(lat, lng, target_lat, target_lng)

    for radius in [500, 1000, 1500, 2000, 2500, 3000, 3500]:
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

            candidates = []
            for element in data.get("elements", []):
                name = element["tags"].get("name")
                center = element.get("center")
                if not name or not center:
                    continue

                if _is_same_name(name, input_name):
                    continue

                diff = bearing_diff(lat, lng, target_lat, target_lng, center["lat"], center["lon"])
                dist_to_origin = geodesic((lat, lng), (center["lat"], center["lon"])).meters

                near_polyline = False
                if trayek_polyline:
                    near_polyline = is_snap_near_polyline(
                        center["lat"], center["lon"], trayek_polyline, threshold_meters=10
                    )

                if near_polyline or (diff <= 105):
                    score = 0 if near_polyline else dist_to_origin
                    candidates.append({
                        "name": name,
                        "lat": center["lat"],
                        "lng": center["lon"],
                        "bearing_diff": round(diff, 2),
                        "dist_to_origin": round(dist_to_origin, 2),
                        "near_polyline": near_polyline,
                        "score": score
                    })

            if candidates:
                best = min(candidates, key=lambda c: c["score"])
                log_snapper_overpass({
                    "action": "overpass_new",
                    "candidates": candidates,
                    "chosen": best
                })
                return best

        except Exception as e:
            print(f"[Overpass Snap] Error: {e}")

    return None


def nominatim_reverse(lat: float, lng: float, input_name: str, target_lat: float, target_lng: float) -> dict | None:
    trayek_polyline = get_trayek_polyline(lat, lng, target_lat, target_lng)

    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "zoom": 18,
        "addressdetails": 1
    }

    try:
        resp = requests.get(NOMINATIM_URL, params=params, timeout=10, headers={"User-Agent": "YourApp/1.0"})
        resp.raise_for_status()
        data = resp.json()

        address = data.get("address", {})
        name = address.get("road") or address.get("neighbourhood") or address.get("suburb")
        if not name:
            return None

        if _is_same_name(name, input_name):
            return None

        diff = bearing_diff(lat, lng, target_lat, target_lng, lat, lng)
        near_polyline = False
        if trayek_polyline:
            near_polyline = is_snap_near_polyline(lat, lng, trayek_polyline, threshold_meters=10)

        if near_polyline or (diff <= 105):
            log_snapper_nominatim({
                "action": "nominatim_resolved",
                "lat": lat,
                "lng": lng,
                "resolved_name": name,
                "full_address": address,
                "bearing_diff": diff,
                "near_polyline": near_polyline
            })

            return {
                "name": name,
                "lat": lat,
                "lng": lng,
                "source": "nominatim"
            }

    except Exception as e:
        print(f"[Nominatim Reverse] Error: {e}")

    return None


def snap_location_pair(from_loc, to_loc, from_lat, from_lng, to_lat, to_lng):
    new_from = {"location": from_loc, "lat": from_lat, "lng": from_lng, "reason": "original"}
    new_to = {"location": to_loc, "lat": to_lat, "lng": to_lng, "reason": "original"}

    from_is_area = is_area(from_loc)
    to_is_area = is_area(to_loc)

    print(f"[Snapper] from_is_area={from_is_area}, to_is_area={to_is_area}")

    if from_is_area and not to_is_area and to_lat and to_lng:
        result = overpass_snap_multi(to_lat, to_lng, to_loc, from_lat, from_lng)
        if not result:
            result = nominatim_reverse(to_lat, to_lng, to_loc, from_lat, from_lng)

        if result:
            new_from.update({
                "location": result["name"],
                "lat": result["lat"],
                "lng": result["lng"],
                "reason": "snap_FROM_luas_TO_sempit"
            })

    elif to_is_area and not from_is_area and from_lat and from_lng:
        result = overpass_snap_multi(from_lat, from_lng, from_loc, to_lat, to_lng)
        if not result:
            result = nominatim_reverse(from_lat, from_lng, from_loc, to_lat, to_lng)

        if result:
            new_to.update({
                "location": result["name"],
                "lat": result["lat"],
                "lng": result["lng"],
                "reason": "snap_TO_luas_FROM_sempit"
            })

    elif from_is_area and to_is_area:
        if from_lat and from_lng:
            result_from = overpass_snap_multi(from_lat, from_lng, from_loc, to_lat, to_lng)
            if not result_from:
                result_from = nominatim_reverse(from_lat, from_lng, from_loc, to_lat, to_lng)

            if result_from:
                new_from.update({
                    "location": result_from["name"],
                    "lat": result_from["lat"],
                    "lng": result_from["lng"],
                    "reason": "snap_FROM_luas_luas"
                })

                result_to = overpass_snap_multi(result_from["lat"], result_from["lng"], to_loc, to_lat, to_lng)
                if not result_to:
                    result_to = nominatim_reverse(result_from["lat"], result_from["lng"], to_loc, to_lat, to_lng)

                if result_to and not _is_same_name(result_to["name"], result_from["name"]):
                    new_to.update({
                        "location": result_to["name"],
                        "lat": result_to["lat"],
                        "lng": result_to["lng"],
                        "reason": "snap_TO_luas_luas"
                    })

    log_snap_location_pair({
        "from_is_area": from_is_area,
        "to_is_area": to_is_area,
        "original_from": from_loc,
        "original_to": to_loc,
        "result_from": new_from,
        "result_to": new_to
    })

    return new_from, new_to
