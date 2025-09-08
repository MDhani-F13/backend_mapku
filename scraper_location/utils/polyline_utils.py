from shapely.geometry import LineString, Point as ShapelyPoint 
import polyline
from scraper_location.utils.google_client import get_directions_polyline
from traffic.utils import can_make_directions_call

def is_snap_near_polyline(snap_lat, snap_lng, encoded_polyline, threshold_meters=200):
    """
    Cek apakah titik snap mendekati trayek polyline (OSRM atau Google).
    """
    points = polyline.decode(encoded_polyline)
    line = LineString(points)
    snap_point = ShapelyPoint(snap_lat, snap_lng)

    distance_deg = snap_point.distance(line)
    # Konversi derajat ke meter kasar: 1 deg ~ 111_000 m
    distance_m = distance_deg * 111_000

    return distance_m <= threshold_meters

def get_or_cache_directions_polyline(segment):
    if segment.route_polyline:
        return segment.route_polyline

    if not can_make_directions_call():
        print("❌ Directions API quota exceeded for this month.")
        return None

    polyline = get_directions_polyline(
        segment.from_lat, segment.from_lng,
        segment.to_lat, segment.to_lng
    )
    if polyline:
        segment.route_polyline = polyline
        segment.save()
    return polyline