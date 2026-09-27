from dataclasses import dataclass
from typing import List, Dict, Optional
import math
import numpy as np
import time

from perception.utils.camera_model import PinholeCamera
from perception.utils.coordinate_utils import meters_to_gps_offset, gps_distance, compute_speed
from perception.detector import Detection
from perception.tracker import Track

@dataclass
class DroneState:
    lat: float
    lon: float
    altitude_m: float
    heading_deg: float
    gimbal_pitch_deg: float

@dataclass
class GeoPoint:
    latitude: float
    longitude: float

@dataclass
class GeoDetection:
    track_id: int
    class_name: str
    latitude: float
    longitude: float
    speed_mps: float
    heading_deg: float
    confidence: float
    timestamp: float

class GeoReferencer:
    def __init__(self, camera: PinholeCamera):
        self.camera = camera
        self.history: Dict[int, List[GeoDetection]] = {}

    def project_to_ground(self, detection: Detection, drone_state: DroneState) -> Optional[GeoPoint]:
        # 1. Get camera ray from bbox center pixel
        ray_c = self.camera.pixel_to_ray(detection.bbox_center[0], detection.bbox_center[1])
        
        # 2. Transform camera ray into drone body frame (Right, Forward, Up)
        # pitch_rad: 0 is horizontal forward, -90 is pointing down (nadir)
        pitch_rad = math.radians(drone_state.gimbal_pitch_deg)
        dx_drone = ray_c[0]
        dy_drone = ray_c[2] * math.cos(pitch_rad) + ray_c[1] * math.sin(pitch_rad)
        dz_drone = ray_c[2] * math.sin(pitch_rad) - ray_c[1] * math.cos(pitch_rad)
        
        # 3. Intersect ray with ground plane (z=0, drone is at +altitude_m)
        if dz_drone >= -1e-6:
            # Ray is parallel to ground or pointing upwards
            return None
            
        t = -drone_state.altitude_m / dz_drone
        
        # Local offsets in drone frame
        dx = dx_drone * t  # Right
        dy = dy_drone * t  # Forward
        
        # 4 & 5. Rotate by drone heading
        heading_rad = math.radians(drone_state.heading_deg)
        # Note: in navigation, heading is CW from North. 
        # Forward is North, Right is East when heading is 0.
        north_offset = dy * math.cos(heading_rad) - dx * math.sin(heading_rad)
        east_offset = dy * math.sin(heading_rad) + dx * math.cos(heading_rad)
        
        # 6. Convert meter offset to GPS
        delta_lat, delta_lon = meters_to_gps_offset(east_offset, north_offset, drone_state.lat)
        
        return GeoPoint(
            latitude=drone_state.lat + delta_lat,
            longitude=drone_state.lon + delta_lon
        )

    def project_detections(self, detections: List[Detection], tracks: List[Track], drone_state: DroneState) -> List[GeoDetection]:
        geo_detections = []
        current_time = time.time()
        
        # Match tracks to detections by bbox (tracker and detector output match directly per frame)
        track_map = {t.bbox_xyxy: t for t in tracks if t.state == 'confirmed'}
        
        for det in detections:
            track = track_map.get(det.bbox_xyxy)
            if not track:
                continue
                
            geo_pt = self.project_to_ground(det, drone_state)
            if not geo_pt:
                continue
                
            speed = 0.0
            heading = 0.0
            
            # Compute speed from history
            if track.track_id in self.history and len(self.history[track.track_id]) > 0:
                prev_geo = self.history[track.track_id][-1]
                dt = current_time - prev_geo.timestamp
                speed = compute_speed((prev_geo.latitude, prev_geo.longitude), 
                                      (geo_pt.latitude, geo_pt.longitude), dt)
                # Could compute object heading here as well
                
            geo_det = GeoDetection(
                track_id=track.track_id,
                class_name=track.class_name,
                latitude=geo_pt.latitude,
                longitude=geo_pt.longitude,
                speed_mps=speed,
                heading_deg=heading,
                confidence=track.confidence,
                timestamp=current_time
            )
            
            if track.track_id not in self.history:
                self.history[track.track_id] = []
            self.history[track.track_id].append(geo_det)
            
            # Keep history bounded
            if len(self.history[track.track_id]) > 10:
                self.history[track.track_id].pop(0)
                
            geo_detections.append(geo_det)
            
        return geo_detections
