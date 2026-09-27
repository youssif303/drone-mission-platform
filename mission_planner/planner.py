from typing import List, Tuple, Optional
from perception.utils.coordinate_utils import gps_distance

# Waypoint: lat, lon, alt
Waypoint = Tuple[float, float, float]

class MissionPlanner:
    def __init__(self, waypoints: List[Waypoint]):
        self.waypoints = waypoints
        self.current_waypoint_index = 0

    def get_current_target(self) -> Optional[Waypoint]:
        if self.is_complete():
            return None
        return self.waypoints[self.current_waypoint_index]

    def advance(self) -> bool:
        if self.is_complete():
            return False
        self.current_waypoint_index += 1
        return not self.is_complete()

    def is_complete(self) -> bool:
        return self.current_waypoint_index >= len(self.waypoints)

    def distance_to_current(self, drone_lat: float, drone_lon: float) -> float:
        target = self.get_current_target()
        if not target:
            return 0.0
        return gps_distance(drone_lat, drone_lon, target[0], target[1])

    def check_waypoint_reached(self, drone_lat: float, drone_lon: float, threshold_m: float = 5.0) -> bool:
        if self.is_complete():
            return False
        dist = self.distance_to_current(drone_lat, drone_lon)
        return dist <= threshold_m
