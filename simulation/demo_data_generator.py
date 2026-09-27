import os
import json
import random
from pathlib import Path
from mission_planner.patterns import grid_pattern
from mission_planner.drone_controller import DemoDroneController

def generate_demo_scenario(name: str, num_frames: int, area_center_lat: float, area_center_lon: float, num_objects: int):
    base_dir = Path(__file__).parent / 'demo_data' / name
    base_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'scenario_name': name,
        'num_frames': num_frames,
        'center_lat': area_center_lat,
        'center_lon': area_center_lon,
        'num_objects': num_objects
    }
    
    with open(base_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
        
    waypoints = grid_pattern(area_center_lat, area_center_lon, 300, 300, 50, 80)
    controller = DemoDroneController(waypoints, speed_mps=15.0)
    controller.takeoff()
    
    # Init synthetic objects
    objects = []
    classes = ['car', 'person']
    for i in range(num_objects):
        obj = {
            'track_id': i + 1,
            'class_name': random.choice(classes),
            'lat': area_center_lat + random.uniform(-0.001, 0.001),
            'lon': area_center_lon + random.uniform(-0.001, 0.001),
            'speed': random.uniform(0, 5),
            'heading': random.uniform(0, 360)
        }
        objects.append(obj)
        
    dt = 1.0 / 10.0 # 10 FPS simulation
    
    with open(base_dir / 'drone_telemetry.jsonl', 'w') as tel_f, open(base_dir / 'detections.jsonl', 'w') as det_f:
        for frame_idx in range(num_frames):
            controller.step(dt)
            state = controller.get_state()
            
            tel_f.write(json.dumps({
                'frame': frame_idx,
                'lat': state.lat,
                'lon': state.lon,
                'altitude_m': state.altitude_m,
                'heading_deg': state.heading_deg,
                'gimbal_pitch_deg': state.gimbal_pitch_deg
            }) + '\n')
            
            frame_detections = []
            for obj in objects:
                # Basic motion model
                obj['lat'] += (obj['speed'] * dt * 0.00001)
                obj['lon'] += (obj['speed'] * dt * 0.00001)
                
                # Mock detection within 100m of drone
                from perception.utils.coordinate_utils import gps_distance
                dist = gps_distance(state.lat, state.lon, obj['lat'], obj['lon'])
                if dist < 100:
                    frame_detections.append({
                        'track_id': obj['track_id'],
                        'class_name': obj['class_name'],
                        'latitude': obj['lat'],
                        'longitude': obj['lon'],
                        'speed_mps': obj['speed'],
                        'heading_deg': obj['heading'],
                        'confidence': random.uniform(0.7, 0.99),
                        'timestamp': frame_idx * dt
                    })
                    
            det_f.write(json.dumps({
                'frame': frame_idx,
                'detections': frame_detections
            }) + '\n')

if __name__ == '__main__':
    generate_demo_scenario('urban_patrol', 300, 48.1351, 11.5820, 8)
    generate_demo_scenario('highway_recon', 200, 48.2000, 11.6000, 5)
    print("Demo scenarios generated successfully.")
