import os
import requests
import asyncio
from scraper_location.utils.quota_tracker import QuotaTracker

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GRAPHHOPPER_API_KEY = os.getenv("GRAPHHOPPER_API_KEY")


def get_directions_polyline(from_lat, from_lng, to_lat, to_lng):
    """
    Google Directions API → dapatkan polyline trayek final.
    """
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{from_lat},{from_lng}",
        "destination": f"{to_lat},{to_lng}",
        "key": GOOGLE_API_KEY
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    routes = r.json().get("routes", [])
    if routes:
        return routes[0]["overview_polyline"]["points"]
    return None


def nearest_roads_snap(lat, lng):
    """
    Google Roads API → snap ke jalan terdekat.
    """
    url = "https://roads.googleapis.com/v1/nearestRoads"
    params = {
        "points": f"{lat},{lng}",
        "key": GOOGLE_API_KEY
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def lookup_place_id(place_id: str):
    """
    Google Place Details → resolve place name dari place_id.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name",
        "key": GOOGLE_API_KEY
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("result", {}).get("name")


def get_osrm_polyline(from_lat, from_lng, to_lat, to_lng):
    """
    OSRM public → trayek kasar polyline (gratis).
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{from_lng},{from_lat};{to_lng},{to_lat}?overview=full&geometries=polyline"
    r = requests.get(url, timeout=5)
    if r.status_code == 200:
        routes = r.json().get("routes", [])
        if routes:
            return routes[0]["geometry"]
    return None

# Buat tracker dedicated
graphhopper_tracker = QuotaTracker(quota_file="logs/graphhopper_quota.json", monthly_limit=15000, daily_limit=500)

last_request_time = None

async def get_graphhopper_polyline(lat1, lng1, lat2, lng2):
    global last_request_time
    GRAPHOPPER_URL = "https://graphhopper.com/api/1/route"
    if not graphhopper_tracker.can_use():
        raise Exception("Graphhopper quota habis!")

    # Rate limit: minimal 3 detik antar request
    if last_request_time:
        elapsed = asyncio.get_event_loop().time() - last_request_time
        if elapsed < 3:
            await asyncio.sleep(3 - elapsed)

    params = {
        "point": [f"{lat1},{lng1}", f"{lat2},{lng2}"],
        "vehicle": "bike",
        "key": GRAPHHOPPER_API_KEY,
        "points_encoded": "true",
        "instructions": "false"
    }

    resp = requests.get(GRAPHOPPER_URL, params=params, timeout=10)
    last_request_time = asyncio.get_event_loop().time()

    resp.raise_for_status()
    graphhopper_tracker.increment()  # catat pemakaian

    data = resp.json()
    path = data["paths"][0]
    return path["points"]