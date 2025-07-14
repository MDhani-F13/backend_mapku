import math

def bearing(lat1, lon1, lat2, lon2):
    dLon = math.radians(lon2 - lon1)
    y = math.sin(dLon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dLon)
    brng = math.atan2(y, x)
    return (math.degrees(brng) + 360) % 360

def bearing_diff(lat1, lon1, lat2, lon2, lat3, lon3):
    b1 = bearing(lat1, lon1, lat2, lon2)
    b2 = bearing(lat1, lon1, lat3, lon3)
    diff = abs(b1 - b2)
    return min(diff, 360 - diff)