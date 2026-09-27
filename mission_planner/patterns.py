import math
from typing import List
from mission_planner.planner import Waypoint
from perception.utils.coordinate_utils import meters_to_gps_offset

def grid_pattern(center_lat: float, center_lon: float, width_m: float, height_m: float, spacing_m: float, altitude: float) -> List[Waypoint]:
    waypoints = []
    
    start_x = -width_m / 2.0
    start_y = -height_m / 2.0
    
    num_lines = int(height_m / spacing_m) + 1
    
    for i in range(num_lines):
        y = start_y + i * spacing_m
        
        if i % 2 == 0:
            x1, x2 = start_x, start_x + width_m
        else:
            x1, x2 = start_x + width_m, start_x
            
        dlat1, dlon1 = meters_to_gps_offset(x1, y, center_lat)
        waypoints.append((center_lat + dlat1, center_lon + dlon1, altitude))
        
        dlat2, dlon2 = meters_to_gps_offset(x2, y, center_lat)
        waypoints.append((center_lat + dlat2, center_lon + dlon2, altitude))
        
    return waypoints

def spiral_pattern(center_lat: float, center_lon: float, max_radius_m: float, spacing_m: float, altitude: float) -> List[Waypoint]:
    waypoints = []
    
    theta = 0.0
    r = 0.0
    
    while r <= max_radius_m:
        dlat, dlon = meters_to_gps_offset(r * math.cos(theta), r * math.sin(theta), center_lat)
        waypoints.append((center_lat + dlat, center_lon + dlon, altitude))
        
        theta += math.pi / 4 # 45 degree steps
        r = (spacing_m * theta) / (2 * math.pi)
        
    return waypoints

def perimeter_pattern(center_lat: float, center_lon: float, radius_m: float, num_points: int, altitude: float) -> List[Waypoint]:
    waypoints = []
    
    for i in range(num_points):
        theta = (2 * math.pi * i) / num_points
        dlat, dlon = meters_to_gps_offset(radius_m * math.cos(theta), radius_m * math.sin(theta), center_lat)
        waypoints.append((center_lat + dlat, center_lon + dlon, altitude))
        
    return waypoints
