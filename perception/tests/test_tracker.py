import pytest
from perception.tracker import MultiObjectTracker
from perception.detector import Detection

def test_tracker_lifecycle():
    tracker = MultiObjectTracker(min_hits=2, max_age=2)
    
    # Frame 1: New detection
    det1 = Detection(class_id=2, class_name='car', bbox_xyxy=(10, 10, 50, 50), confidence=0.9, bbox_center=(30, 30))
    tracks = tracker.update([det1])
    assert len(tracks) == 1
    assert tracks[0].state == 'tentative'
    assert tracks[0].hits == 1
    
    # Frame 2: Matched detection
    det2 = Detection(class_id=2, class_name='car', bbox_xyxy=(12, 12, 52, 52), confidence=0.9, bbox_center=(32, 32))
    tracks = tracker.update([det2])
    assert len(tracks) == 1
    assert tracks[0].state == 'confirmed' # min_hits=2
    assert tracks[0].hits == 2
    
    # Frame 3: Missed detection
    tracks = tracker.update([])
    assert len(tracks) == 1
    assert tracks[0].state == 'confirmed'
    assert tracks[0].time_since_update == 1
    
    # Frame 4: Missed detection again
    tracks = tracker.update([])
    assert len(tracks) == 1
    assert tracks[0].time_since_update == 2
    
    # Frame 5: Missed detection again - should be lost and removed
    tracks = tracker.update([])
    assert len(tracks) == 0
