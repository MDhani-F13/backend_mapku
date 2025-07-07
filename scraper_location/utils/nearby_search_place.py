import os
import requests
from geopy.distance import geodesic
from scraper_location.utils.quota_tracker import QuotaTracker
from scraper_location.core.logger import log_pair_sanity

tracker = QuotaTracker()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

OSM_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def haversine_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).km

def search_google_nearby(name, lat, lng):
    """
    Google Nearby Search untuk cari nama di sekitar lat/lng.
    Return dict kalau ketemu.
    """
    if not tracker.can_use():
        return None

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 2000,
        "keyword": name,
        "key": GOOGLE_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("results"):
            place = data["results"][0]
            place_name = place["name"]
            place_loc = place["geometry"]["location"]
            tracker.increment()
            return {
                "location": place_name,
                "lat": place_loc["lat"],
                "lng": place_loc["lng"],
                "source": "google"
            }
    except Exception as e:
        print(f"[search_google_nearby] Google API error: {e}")

    return None

def search_osm_nearby(name, lat, lng):
    """
    OSM Nominatim Search fallback.
    """
    try:
        params = {
            "q": name,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "extratags": 1,
            "viewbox": f"{lng-0.02},{lat-0.02},{lng+0.02},{lat+0.02}",
            "bounded": 1
        }
        headers = {"User-Agent": "location-validator/1.0"}
        resp = requests.get(OSM_NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            osm = data[0]
            return {
                "location": osm.get("display_name", name),
                "lat": float(osm["lat"]),
                "lng": float(osm["lon"]),
                "source": "osm"
            }
    except Exception as e:
        print(f"[search_osm_nearby] OSM fallback error: {e}")

    return None

def find_nearby_same_name(name, lat, lng):
    """
    Wrapper: coba OSM dulu ➜ fallback ke Google Nearby.
    """
    result = search_osm_nearby(name, lat, lng)
    if result:
        return result

    result = search_google_nearby(name, lat, lng)
    if result:
        return result

    return None

def check_pair_sanity(from_name, to_name, from_lat, from_lng, to_lat, to_lng, distance_threshold_km=8):
    """
    Validasi jarak from-to ➜ kalau jauh ➜ cari nearby same-name.
    Return updated from & to.
    """
    new_from = {"location": from_name, "lat": from_lat, "lng": from_lng}
    new_to = {"location": to_name, "lat": to_lat, "lng": to_lng}

    if None in [from_lat, from_lng, to_lat, to_lng]:
        return new_from, new_to

    distance = haversine_distance(from_lat, from_lng, to_lat, to_lng)

    if distance <= distance_threshold_km:
        return new_from, new_to

    print(f"[check_pair_sanity] ⚠️ Distance too far ({distance:.2f} km), trying recheck nearby same-name.")

    nearby_from = find_nearby_same_name(to_name, from_lat, from_lng)
    if nearby_from:
        new_from.update(nearby_from)

    nearby_to = find_nearby_same_name(from_name, to_lat, to_lng)
    if nearby_to:
        new_to.update(nearby_to)

    new_distance = haversine_distance(new_from["lat"], new_from["lng"], new_to["lat"], new_to["lng"])

    log_pair_sanity({
        "from_loc_before" : from_name,
        "to_loc_before" : to_name,
        "from_loc_after" : new_from["location"],
        "to_loc_after" : new_to["location"],
        "from_lat_before": from_lat,
        "from_lng_before": from_lng,
        "to_lat_before": to_lat,
        "to_lng_before": to_lng,
        "from_lat_after": new_from["lat"],
        "from_lng_after": new_from["lng"],
        "to_lat_after": new_to["lat"],
        "to_lng_after": new_to["lng"],
        "initial_distance_km": distance,
        "latest_distance_km": new_distance,
    })
        
    return new_from, new_to