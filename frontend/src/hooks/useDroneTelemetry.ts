import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { DroneState } from '../types';

export function useDroneTelemetry() {
  const { data, isConnected } = useWebSocket<any>('/ws/drone-telemetry');
  const [droneState, setDroneState] = useState<DroneState>({
    lat: 48.1351,
    lon: 11.5820,
    alt: 50.0,
    speed: 12.5,
    heading: 90.0,
    battery: 94.0,
    status: 'ACTIVE',
    timestamp: new Date().toISOString(),
  });

  useEffect(() => {
    if (data && typeof data === 'object') {
      const lat = data.lat ?? data.latitude ?? 48.1351;
      const lon = data.lon ?? data.longitude ?? 11.5820;
      const alt = data.alt ?? data.altitude_m ?? 50.0;
      const speed = data.speed ?? data.speed_mps ?? 12.5;
      const heading = data.heading ?? data.heading_deg ?? 90.0;
      const battery = data.battery ?? data.battery_percent ?? 94.0;
      const status = data.status ?? 'ACTIVE';
      const timestamp = data.timestamp ? String(data.timestamp) : new Date().toISOString();

      setDroneState({
        lat: Number(lat) || 48.1351,
        lon: Number(lon) || 11.5820,
        alt: Number(alt) || 50.0,
        speed: Number(speed) || 0.0,
        heading: Number(heading) || 0.0,
        battery: Number(battery) || 100.0,
        status,
        timestamp,
      });
    }
  }, [data]);

  const hasTelemetry = data !== null && typeof data === 'object';

  return { droneState, isConnected, hasTelemetry };
}
