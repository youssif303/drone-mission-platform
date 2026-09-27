export type MissionStatus = 'pending' | 'active' | 'paused' | 'completed' | 'aborted';

export interface Waypoint {
  lat: number;
  lon: number;
  alt: number;
  action?: string;
  reached?: boolean;
}

export interface Mission {
  id: number;
  name: string;
  description?: string;
  status: MissionStatus;
  waypoints: Waypoint[];
  created_at: string;
}

export interface TrackHistoryPoint {
  lat: number;
  lon: number;
  timestamp: string;
}

export interface TrackedObject {
  id: number;
  class_name: string;
  lat: number;
  lon: number;
  speed: number;
  heading: number;
  status: string;
  last_seen: string;
  history?: TrackHistoryPoint[];
}

export interface GeoDetection {
  track_id: number;
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
  lat: number;
  lon: number;
  speed?: number;
  heading?: number;
  timestamp: string;
}

export interface Detection extends GeoDetection {}

export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertType = 'detection' | 'system' | 'geofence' | 'health';

export interface Alert {
  id: number;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  timestamp: string;
  track_id?: number;
}

export interface AlertRule {
  id: number;
  name: string;
  type: AlertType;
  severity: AlertSeverity;
  condition: any;
}

export interface DroneState {
  lat: number;
  lon: number;
  alt: number;
  speed: number;
  heading: number;
  battery: number;
  status: string;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  components: Record<string, string>;
  last_check: string;
}
