import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _full_path(filename):
    return os.path.join(BASE_DIR, f"logs/{filename}")


def load_cache(filename):
    path = _full_path(filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_cache(filename, data):
    path = _full_path(filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_polyline(filename, from_loc=None, to_loc=None,
                 from_lat=None, from_lng=None, to_lat=None, to_lng=None):
    cache = load_cache(filename)
    for item in cache:
        same_coords = (
            round(item["from_lat"], 5) == round(from_lat, 5) and
            round(item["from_lng"], 5) == round(from_lng, 5) and
            round(item["to_lat"], 5) == round(to_lat, 5) and
            round(item["to_lng"], 5) == round(to_lng, 5)
        )
        if filename == "polyline_final_cache.json":
            if item["from"] == from_loc and item["to"] == to_loc and same_coords:
                return item["polyline"]
        else:
            if same_coords:
                return item["polyline"]
    return None


def save_polyline(filename, from_loc=None, to_loc=None,
                  from_lat=None, from_lng=None, to_lat=None, to_lng=None, polyline=None):
    cache = load_cache(filename)
    for item in cache:
        same_coords = (
            round(item["from_lat"], 5) == round(from_lat, 5) and
            round(item["from_lng"], 5) == round(from_lng, 5) and
            round(item["to_lat"], 5) == round(to_lat, 5) and
            round(item["to_lng"], 5) == round(to_lng, 5)
        )
        if filename == "polyline_final_cache.json":
            if item["from"] == from_loc and item["to"] == to_loc and same_coords:
                return  # sudah ada
        else:
            if same_coords:
                return  # sudah ada

    data = {
        "from_lat": from_lat,
        "from_lng": from_lng,
        "to_lat": to_lat,
        "to_lng": to_lng,
        "polyline": polyline
    }
    if filename == "polyline_final_cache.json":
        data["from"] = from_loc
        data["to"] = to_loc

    cache.append(data)
    save_cache(filename, cache)
