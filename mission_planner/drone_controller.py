from abc import ABC, abstractmethod
from typing import List, Optional
from perception.geo_reference import DroneState
from mission_planner.planner import Waypoint, MissionPlanner
from perception.utils.coordinate_utils import gps_bearing, gps_distance, meters_to_gps_offset
import math

class DroneController(ABC):
    @abstractmethod
    def move_to(self, lat: float, lon: float, alt: float):
        pass
        
    @abstractmethod
    def get_state(self) -> DroneState:
        pass
        
    @abstractmethod
    def takeoff(self):
        pass
        
    @abstractmethod
    def land(self):
        pass

class DemoDroneController(DroneController):
    def __init__(self, waypoints: List[Waypoint], speed_mps: float = 10.0):
        self.planner = MissionPlanner(waypoints)
        self.speed_mps = speed_mps
        
        start_wp = waypoints[0] if waypoints else (0.0, 0.0, 0.0)
        
        self.state = DroneState(
            lat=start_wp[0],
            lon=start_wp[1],
            altitude_m=0.0,
            heading_deg=0.0,
            gimbal_pitch_deg=-45.0
        )
        self.battery = 100.0
        self.is_flying = False

    def move_to(self, lat: float, lon: float, alt: float):
        pass # Managed by step()

    def get_state(self) -> DroneState:
        return self.state

    def takeoff(self):
        self.is_flying = True
        target = self.planner.get_current_target()
        if target:
            self.state.altitude_m = target[2]

    def land(self):
        self.is_flying = False
        self.state.altitude_m = 0.0

    def step(self, dt: float):
        if not self.is_flying or self.planner.is_complete():
            return
            
        target = self.planner.get_current_target()
        if not target:
            return
            
        t_lat, t_lon, t_alt = target
        
        dist = self.planner.distance_to_current(self.state.lat, self.state.lon)
        if dist <= 1.0:
            self.planner.advance()
            return
            
        bearing = gps_bearing(self.state.lat, self.state.lon, t_lat, t_lon)
        self.state.heading_deg = bearing
        
        # Move drone
        dist_to_move = self.speed_mps * dt
        if dist_to_move > dist:
            dist_to_move = dist
            
        dx = dist_to_move * math.sin(math.radians(bearing))
        dy = dist_to_move * math.cos(math.radians(bearing))
        
        dlat, dlon = meters_to_gps_offset(dx, dy, self.state.lat)
        
        self.state.lat += dlat
        self.state.lon += dlon
        self.state.altitude_m = t_alt
        
        # Simulate battery drain
        self.battery -= 0.01 * dt
