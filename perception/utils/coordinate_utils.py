import math
from typing import Tuple

# WGS84 Constants
R_EARTH = 6378137.0 # Earth radius in meters

def meters_to_gps_offset(dx_meters: float, dy_meters: float, ref_lat: float) -> Tuple[float, float]:
    '''
    Convert local meter offset to GPS delta (lat, lon).
    dx_meters: offset along longitude (East-West)
    dy_meters: offset along latitude (North-South)
    '''
    delta_lat = math.degrees(dy_meters / R_EARTH)
    r_earth_at_lat = R_EARTH * math.cos(math.radians(ref_lat))
    delta_lon = math.degrees(dx_meters / r_earth_at_lat)
    return delta_lat, delta_lon

def gps_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    '''
    Haversine distance in meters between two GPS points.
    '''
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R_EARTH * c

def gps_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    '''
    Bearing in degrees from point 1 to point 2.
    '''
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    diff_lon = math.radians(lon2 - lon1)
    
    x = math.sin(diff_lon) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - (math.sin(lat1_r) * math.cos(lat2_r) * math.cos(diff_lon))
    
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    return (initial_bearing + 360) % 360

def compute_speed(pos1: Tuple[float, float], pos2: Tuple[float, float], dt: float) -> float:
    '''
    Compute speed in m/s between two GPS points given delta time dt.
    pos = (lat, lon)
    '''
    if dt <= 0:
        return 0.0
    dist = gps_distance(pos1[0], pos1[1], pos2[0], pos2[1])
    return dist / dt
