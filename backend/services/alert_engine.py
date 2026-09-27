import json
from typing import List, Dict
from backend.models.alert import AlertDB, AlertRuleDB
from backend.models.detection import GeoDetection

class AlertEngine:
    def __init__(self):
        pass

    def check_zone_intrusion(self, detection: GeoDetection, rules: List[AlertRuleDB]) -> List[AlertDB]:
        alerts = []
        for rule in rules:
            if rule.rule_type != "zone_intrusion" or not rule.enabled:
                continue
            
            params = json.loads(rule.params_json)
            polygon = params.get("polygon", [])
            
            if len(polygon) < 3:
                continue
                
            # Simple ray-casting algorithm for point in polygon
            x = detection.longitude
            y = detection.latitude
            
            inside = False
            j = len(polygon) - 1
            for i in range(len(polygon)):
                xi, yi = polygon[i]
                xj, yj = polygon[j]
                
                intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-10) + xi)
                if intersect:
                    inside = not inside
                j = i
                
            if inside:
                alerts.append(AlertDB(
                    alert_type="zone_intrusion",
                    severity="critical",
                    message=f"Intrusion detected in zone: {rule.name}",
                    track_id=detection.track_id,
                    latitude=detection.latitude,
                    longitude=detection.longitude,
                    timestamp=detection.timestamp
                ))
        return alerts

    def check_speed_violation(self, detection: GeoDetection, rules: List[AlertRuleDB]) -> List[AlertDB]:
        alerts = []
        for rule in rules:
            if rule.rule_type != "speed_violation" or not rule.enabled:
                continue
                
            params = json.loads(rule.params_json)
            max_speed = params.get("max_speed_mps", 0.0)
            
            if detection.speed_mps > max_speed:
                alerts.append(AlertDB(
                    alert_type="speed_violation",
                    severity="warning",
                    message=f"Speed violation: {detection.speed_mps:.1f} m/s exceeds {max_speed:.1f} m/s",
                    track_id=detection.track_id,
                    latitude=detection.latitude,
                    longitude=detection.longitude,
                    timestamp=detection.timestamp
                ))
        return alerts

    def check_new_object(self, track_id: int, known_tracks: set) -> List[AlertDB]:
        alerts = []
        if track_id not in known_tracks:
            alerts.append(AlertDB(
                alert_type="new_object",
                severity="info",
                message=f"New object detected: Track {track_id}",
                track_id=track_id,
                timestamp=__import__('datetime').datetime.utcnow()
            ))
            known_tracks.add(track_id)
        return alerts

    def process_detection(self, geo_detection: GeoDetection, rules: List[AlertRuleDB], known_tracks: set) -> List[AlertDB]:
        alerts = []
        alerts.extend(self.check_zone_intrusion(geo_detection, rules))
        alerts.extend(self.check_speed_violation(geo_detection, rules))
        alerts.extend(self.check_new_object(geo_detection.track_id, known_tracks))
        return alerts
