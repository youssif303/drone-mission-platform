from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    # Fallback for testing environments without ultralytics
    YOLO = None

@dataclass
class Detection:
    class_id: int
    class_name: str
    bbox_xyxy: Tuple[float, float, float, float]
    confidence: float
    bbox_center: Tuple[float, float]

class ObjectDetector:
    # Map COCO class IDs to simplified classes
    ALLOWED_CLASSES = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}

    def __init__(self, model_path: str = 'yolov8s.pt', conf_threshold: float = 0.35, device: str = 'cpu'):
        self.conf_threshold = conf_threshold
        if YOLO is not None:
            self.model = YOLO(model_path)
            self.model.to(device)
        else:
            self.model = None
            
    def detect(self, frame: np.ndarray) -> List[Detection]:
        if self.model is None:
            return []
            
        results = self.model(frame, verbose=False)[0]
        detections = []
        
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < self.conf_threshold:
                continue
                
            cls_id = int(box.cls[0])
            if cls_id not in self.ALLOWED_CLASSES:
                continue
                
            xyxy = box.xyxy[0].cpu().numpy().tolist()
            cx = (xyxy[0] + xyxy[2]) / 2.0
            cy = (xyxy[1] + xyxy[3]) / 2.0
            
            det = Detection(
                class_id=cls_id,
                class_name=self.ALLOWED_CLASSES[cls_id],
                bbox_xyxy=tuple(xyxy),
                confidence=conf,
                bbox_center=(cx, cy)
            )
            detections.append(det)
            
        return detections
