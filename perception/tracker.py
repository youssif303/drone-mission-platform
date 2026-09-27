from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment
from perception.detector import Detection

@dataclass
class Track:
    track_id: int
    class_name: str
    bbox_xyxy: Tuple[float, float, float, float]
    confidence: float
    age: int
    hits: int
    time_since_update: int
    velocity_px: Tuple[float, float]
    state: str  # 'tentative', 'confirmed', 'lost'

def compute_iou(boxA: Tuple[float, float, float, float], boxB: Tuple[float, float, float, float]) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

class MultiObjectTracker:
    def __init__(self, max_age: int = 30, min_hits: int = 3, iou_threshold: float = 0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self._next_id = 1

    def update(self, detections: List[Detection]) -> List[Track]:
        # 1. Compute IoU matrix
        num_tracks = len(self.tracks)
        num_detections = len(detections)
        
        iou_matrix = np.zeros((num_tracks, num_detections), dtype=np.float32)
        for t, track in enumerate(self.tracks):
            for d, det in enumerate(detections):
                if track.class_name == det.class_name:
                    iou_matrix[t, d] = compute_iou(track.bbox_xyxy, det.bbox_xyxy)

        # 2. Hungarian algorithm (minimize cost = 1 - iou)
        cost_matrix = 1.0 - iou_matrix
        matched_indices = []
        if num_tracks > 0 and num_detections > 0:
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            for r, c in zip(row_ind, col_ind):
                if iou_matrix[r, c] >= self.iou_threshold:
                    matched_indices.append((r, c))

        matched_tracks = set(r for r, c in matched_indices)
        matched_detections = set(c for r, c in matched_indices)

        # 3. Update matched tracks
        for r, c in matched_indices:
            track = self.tracks[r]
            det = detections[c]
            
            # Estimate velocity
            old_cx = (track.bbox_xyxy[0] + track.bbox_xyxy[2]) / 2.0
            old_cy = (track.bbox_xyxy[1] + track.bbox_xyxy[3]) / 2.0
            new_cx = det.bbox_center[0]
            new_cy = det.bbox_center[1]
            track.velocity_px = (new_cx - old_cx, new_cy - old_cy)
            
            track.bbox_xyxy = det.bbox_xyxy
            track.confidence = det.confidence
            track.hits += 1
            track.time_since_update = 0
            
            if track.state == 'tentative' and track.hits >= self.min_hits:
                track.state = 'confirmed'

        # 4. Create new tracks for unmatched detections
        for d, det in enumerate(detections):
            if d not in matched_detections:
                new_track = Track(
                    track_id=self._next_id,
                    class_name=det.class_name,
                    bbox_xyxy=det.bbox_xyxy,
                    confidence=det.confidence,
                    age=0,
                    hits=1,
                    time_since_update=0,
                    velocity_px=(0.0, 0.0),
                    state='tentative'
                )
                self.tracks.append(new_track)
                self._next_id += 1

        # 5. Age unmatched existing tracks, delete old ones
        for t in range(num_tracks):
            if t not in matched_tracks:
                track = self.tracks[t]
                track.time_since_update += 1
                if track.time_since_update > self.max_age:
                    track.state = 'lost'
                elif track.state == 'tentative':
                    track.state = 'lost'

        for track in self.tracks:
            track.age += 1

        self.tracks = [t for t in self.tracks if t.state != 'lost']
        return self.tracks
