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
