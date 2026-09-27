import cv2
import numpy as np
from dataclasses import dataclass
from typing import List

from perception.detector import ObjectDetector, Detection
from perception.tracker import MultiObjectTracker, Track
from perception.geo_reference import GeoReferencer, GeoDetection, DroneState
from perception.utils.camera_model import PinholeCamera

@dataclass
class PerceptionResult:
    detections: List[Detection]
    tracks: List[Track]
    geo_detections: List[GeoDetection]
    annotated_frame: np.ndarray

class PerceptionPipeline:
    def __init__(self, model_path: str, camera_fov: float, conf_threshold: float, image_width: int = 1920, image_height: int = 1080):
        self.detector = ObjectDetector(model_path=model_path, conf_threshold=conf_threshold)
        self.tracker = MultiObjectTracker()
        camera = PinholeCamera.from_fov(camera_fov, image_width, image_height)
        self.geo_referencer = GeoReferencer(camera)

    def process_frame(self, frame: np.ndarray, drone_state: DroneState) -> PerceptionResult:
        detections = self.detector.detect(frame)
        tracks = self.tracker.update(detections)
        geo_detections = self.geo_referencer.project_detections(detections, tracks, drone_state)
        annotated_frame = self.draw_detections(frame, tracks)
        
        return PerceptionResult(
            detections=detections,
            tracks=tracks,
            geo_detections=geo_detections,
            annotated_frame=annotated_frame
        )

    def draw_detections(self, frame: np.ndarray, tracks: List[Track]) -> np.ndarray:
        annotated = frame.copy()
        for track in tracks:
            if track.state != 'confirmed':
                continue
                
            x1, y1, x2, y2 = map(int, track.bbox_xyxy)
            color = (0, 255, 0) # Green for confirmed
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            label = f"ID:{track.track_id} {track.class_name} {track.confidence:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - 20), (x1 + w, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
        return annotated
