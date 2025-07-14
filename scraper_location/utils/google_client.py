import requests, os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

def get_directions_polyline(from_lat, from_lng, to_lat, to_lng):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{from_lat},{from_lng}",
        "destination": f"{to_lat},{to_lng}",
        "key": GOOGLE_API_KEY
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        routes = r.json().get("routes", [])
        if routes:
            return routes[0]["overview_polyline"]["points"]
    return None

def nearest_roads_snap(lat, lng):
    """Call Google Roads API for nearest road to a point."""
    url = "https://roads.googleapis.com/v1/nearestRoads"
    params = {
        "points": f"{lat},{lng}",
        "key": GOOGLE_API_KEY
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def lookup_place_id(place_id: str):
    """Call Google Place Details API to get place name from place_id."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name",
        "key": GOOGLE_API_KEY
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    result = data.get("result", {})
    return result.get("name")
