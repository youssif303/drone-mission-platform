import pytest
import numpy as np
from perception.detector import ObjectDetector

def test_object_detector_initialization():
    detector = ObjectDetector(model_path='dummy.pt', device='cpu')
    assert detector.conf_threshold == 0.35
    assert detector.model is None # Since we don't load real ultralytics for test fallback

def test_object_detector_fallback():
    detector = ObjectDetector(model_path='dummy.pt', device='cpu')
    detector.model = None # Force fallback behavior
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(frame)
    
    assert isinstance(detections, list)
    assert len(detections) == 0
