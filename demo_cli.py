"""
Drone Mission Planning & Perception Platform — Interactive CLI Demo
Run this script to simulate a live drone mission with real-time perception and geo-referencing.
"""

import time
import numpy as np
from mission_planner.patterns import grid_pattern
from mission_planner.drone_controller import DemoDroneController
from perception.pipeline import PerceptionPipeline
from perception.detector import Detection
from perception.utils.coordinate_utils import gps_distance

def run_mission_demo():
    print("=" * 70)
    print("[MISSION] DRONE MISSION PLANNING & PERCEPTION PLATFORM - LIVE CLI SIMULATION")
    print("=" * 70)
    
    # 1. Generate autonomous search pattern (Lawnmower Grid)
    center_lat = 48.1351
    center_lon = 11.5820
    print(f"[*] Planning Autonomous Search Grid around ({center_lat}, {center_lon})...")
    waypoints = grid_pattern(center_lat, center_lon, width_m=300, height_m=200, spacing_m=50, altitude=50.0)
    print(f"[+] Generated {len(waypoints)} waypoints for area surveillance.")
    
    # 2. Initialize flight controller & perception pipeline
    controller = DemoDroneController(waypoints, speed_mps=15.0)
    controller.takeoff()
    
    pipeline = PerceptionPipeline(
        model_path="yolov8s.pt",
        camera_fov=90.0,
        conf_threshold=0.35,
        image_width=1280,
        image_height=720
    )
    
    print("[*] Taking off... Drone climbing to 50m AGL.")
    print("[*] Activating Perception Engine (Detection + ByteTrack + Geo-Referencing)...")
    print("-" * 70)
    print(f"{'SEC':<4} | {'DRONE GPS':<24} | {'ALT':<5} | {'BAT':<4} | {'TARGETS (Class, GPS, Speed)':<32}")
    print("-" * 70)
    
    # Pre-defined ground objects moving in area
    ground_objects = [
        {"class_id": 2, "class_name": "car", "center": [600, 360], "vel": [2, 1]},
        {"class_id": 0, "class_name": "person", "center": [400, 280], "vel": [-1, 0]},
        {"class_id": 7, "class_name": "truck", "center": [750, 480], "vel": [3, -1]}
    ]
    
    dt = 1.0  # 1 second time step
    for step in range(1, 16):
        # Update drone flight physics
        controller.step(dt)
        drone_state = controller.get_state()
        
        # Simulate video frame & detections
        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        simulated_detections = []
        for obj in ground_objects:
            obj["center"][0] = (obj["center"][0] + obj["vel"][0]) % 1200 + 40
            obj["center"][1] = (obj["center"][1] + obj["vel"][1]) % 640 + 40
            cx, cy = obj["center"]
            simulated_detections.append(
                Detection(
                    class_id=obj["class_id"],
                    class_name=obj["class_name"],
                    bbox_xyxy=(cx - 20, cy - 20, cx + 20, cy + 20),
                    confidence=0.92,
                    bbox_center=(float(cx), float(cy))
                )
            )
        
        # Run tracking & geo-referencing
        tracks = pipeline.tracker.update(simulated_detections)
        geo_detections = pipeline.geo_referencer.project_detections(simulated_detections, tracks, drone_state)
        
        # Format target report
        target_summaries = []
        for gd in geo_detections:
            dist = gps_distance(drone_state.lat, drone_state.lon, gd.latitude, gd.longitude)
            target_summaries.append(f"#{gd.track_id} {gd.class_name} ({dist:.1f}m away)")
        
        targets_str = ", ".join(target_summaries) if target_summaries else "Scanning..."
        drone_loc = f"{drone_state.lat:.5f}N, {drone_state.lon:.5f}E"
        
        print(f"{step:>3}s | {drone_loc:<24} | {drone_state.altitude_m:>4.0f}m | {controller.battery:>3.0f}% | {targets_str}")
        time.sleep(0.3)
        
    print("-" * 70)
    print("[SUCCESS] Flight simulation completed. All sensor telemetry and targets logged.")
    print("[WEB APP] To view the interactive web dashboard with maps and live video:")
    print("          Open http://localhost:3000 in your web browser.")
    print("=" * 70)

if __name__ == "__main__":
    run_mission_demo()
