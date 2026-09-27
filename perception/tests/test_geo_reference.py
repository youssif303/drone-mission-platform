import pytest
import math
from perception.geo_reference import GeoReferencer, DroneState
from perception.utils.camera_model import PinholeCamera
from perception.detector import Detection

def test_geo_referencer_nadir():
    camera = PinholeCamera.from_fov(90.0, 1000, 1000)
    referencer = GeoReferencer(camera)
    
    drone_state = DroneState(lat=48.1, lon=11.6, altitude_m=50.0, heading_deg=0.0, gimbal_pitch_deg=-90.0)
    
    # Detection at image center
    det = Detection(class_id=0, class_name='person', bbox_xyxy=(490, 490, 510, 510), confidence=0.9, bbox_center=(500, 500))
    
    geo_pt = referencer.project_to_ground(det, drone_state)
    assert geo_pt is not None
    assert pytest.approx(geo_pt.latitude, abs=1e-5) == 48.1
    assert pytest.approx(geo_pt.longitude, abs=1e-5) == 11.6

def test_geo_referencer_offset():
    camera = PinholeCamera.from_fov(90.0, 1000, 1000)
    referencer = GeoReferencer(camera)
    
    drone_state = DroneState(lat=48.1, lon=11.6, altitude_m=50.0, heading_deg=0.0, gimbal_pitch_deg=-90.0)
    
    # Detection offset (y=250 is top of image, forward in camera coords)
    det = Detection(class_id=0, class_name='person', bbox_xyxy=(490, 240, 510, 260), confidence=0.9, bbox_center=(500, 250))
    
    geo_pt = referencer.project_to_ground(det, drone_state)
    assert geo_pt is not None
    
    # Object is forward (North since heading=0)
    assert geo_pt.latitude > 48.1
    # Very little offset in longitude (should be approx 11.6)
    assert pytest.approx(geo_pt.longitude, abs=1e-5) == 11.6
