import React, { useEffect, useState, useRef, useMemo } from 'react';
import GeoThreatMap from '../components/GeoThreatMap/GeoThreatMap';
import VideoFeed from '../components/VideoFeed/VideoFeed';
import DroneStatus from '../components/DroneStatus/DroneStatus';
import TrackingTable from '../components/TrackingTable/TrackingTable';
import AlertTimeline from '../components/AlertTimeline/AlertTimeline';
import MissionProgress from '../components/MissionProgress/MissionProgress';

import { useDetections } from '../hooks/useDetections';
import { useDroneTelemetry } from '../hooks/useDroneTelemetry';
import { useAlerts } from '../hooks/useAlerts';
import { useAppStore } from '../store/appStore';
import { getMissions, getTracks } from '../services/api';
import { TrackedObject, Alert, DroneState, Mission, MissionStatus, Waypoint } from '../types';

// Distance in meters between two GPS coordinates (Haversine)
function getDistanceMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

// Bearing in degrees from point 1 to point 2
function getBearing(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const lat1Rad = (lat1 * Math.PI) / 180;
  const lat2Rad = (lat2 * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const y = Math.sin(dLon) * Math.cos(lat2Rad);
  const x =
    Math.cos(lat1Rad) * Math.sin(lat2Rad) -
    Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);
  const brng = (Math.atan2(y, x) * 180) / Math.PI;
  return (brng + 360) % 360;
}

export default function Dashboard() {
  const { detections, isConnected: isDetectConnected } = useDetections();
  const { droneState: wsDroneState, isConnected: isTelemetryConnected } = useDroneTelemetry();
  const { alerts: wsAlerts, isConnected: isAlertsConnected } = useAlerts();

  const { activeMission, selectedTrackId, actions } = useAppStore();

  // Active simulated or WS drone state
  const [droneState, setDroneState] = useState<DroneState>({
    lat: 48.1340,
    lon: 11.5800,
    alt: 50.0,
    speed: 14.5,
    heading: 68.0,
    battery: 96.0,
    status: 'ACTIVE',
    timestamp: new Date().toISOString(),
  });

  const [tracks, setTracks] = useState<TrackedObject[]>([
    {
      id: 1,
      class_name: 'car',
      lat: 48.1348,
      lon: 11.5815,
      speed: 35.0,
      heading: 85.0,
      status: 'confirmed',
      last_seen: new Date().toISOString(),
    },
    {
      id: 2,
      class_name: 'person',
      lat: 48.1355,
      lon: 11.5825,
      speed: 4.2,
      heading: 12.0,
      status: 'confirmed',
      last_seen: new Date().toISOString(),
    },
    {
      id: 3,
      class_name: 'truck',
      lat: 48.1360,
      lon: 11.5830,
      speed: 28.5,
      heading: 180.0,
      status: 'confirmed',
      last_seen: new Date().toISOString(),
    }
  ]);

  const [alerts, setAlerts] = useState<Alert[]>([
    {
      id: 1,
      type: 'detection',
      severity: 'info',
      message: 'Autonomous patrol pattern initiated. 4 waypoints queued.',
      timestamp: new Date().toISOString(),
    },
    {
      id: 2,
      type: 'geofence',
      severity: 'warning',
      message: 'Target #1 (CAR) approaching perimeter boundary.',
      timestamp: new Date().toISOString(),
    }
  ]);

  const currentWpIndexRef = useRef<number>(0);

  // Sync live connection status
  useEffect(() => {
    const isLive = isDetectConnected || isTelemetryConnected || isAlertsConnected;
    useAppStore.getState().actions.setIsLive(isLive);
  }, [isDetectConnected, isTelemetryConnected, isAlertsConnected]);

  // Sync WebSocket alerts
  useEffect(() => {
    if (wsAlerts && wsAlerts.length > 0) {
      setAlerts(wsAlerts);
    }
  }, [wsAlerts]);

  // Fetch or initialize active mission on mount
  useEffect(() => {
    const defaultMission: Mission = {
      id: 1,
      name: 'Alpha Recon Patrol',
      description: 'Autonomous area perimeter surveillance',
      status: 'active',
      created_at: new Date().toISOString(),
      waypoints: [
        { lat: 48.1340, lon: 11.5800, alt: 50, action: 'Surveillance', reached: false },
        { lat: 48.1345, lon: 11.5815, alt: 50, action: 'Scan Target', reached: false },
        { lat: 48.1355, lon: 11.5825, alt: 50, action: 'Perimeter Check', reached: false },
        { lat: 48.1360, lon: 11.5830, alt: 50, action: 'Return', reached: false },
      ]
    };

    // 1. Check if store already has a newly planned active mission
    const currentStoreMission = useAppStore.getState().activeMission;
    if (currentStoreMission && currentStoreMission.waypoints && currentStoreMission.waypoints.length > 0) {
      currentWpIndexRef.current = 0;
      const firstWp = currentStoreMission.waypoints[0];
      setDroneState(prev => ({
        ...prev,
        lat: firstWp.lat,
        lon: firstWp.lon,
      }));
      return;
    }

    // 2. Check localStorage cache
    try {
      const cached = localStorage.getItem('cached_active_mission');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (parsed && Array.isArray(parsed.waypoints) && parsed.waypoints.length > 0) {
          actions.setActiveMission(parsed);
          currentWpIndexRef.current = 0;
          setDroneState(prev => ({
            ...prev,
            lat: parsed.waypoints[0].lat,
            lon: parsed.waypoints[0].lon,
          }));
          return;
        }
      }
    } catch (e) {}

    // 3. Otherwise fetch from backend API
    getMissions().then(missions => {
      if (Array.isArray(missions) && missions.length > 0) {
        const savedId = localStorage.getItem('active_mission_id');
        let chosen = savedId ? missions.find(m => String(m.id) === savedId) : undefined;
        if (!chosen) {
          chosen = missions.find(m => m.status === 'active') || missions[0];
        }

        const normalizedWaypoints: Waypoint[] = (chosen.waypoints || []).map((wp: any, idx: number) => ({
          lat: Number(wp.lat ?? wp.latitude),
          lon: Number(wp.lon ?? wp.longitude),
          alt: Number(wp.alt ?? wp.altitude ?? 50),
          action: wp.action || `Waypoint #${idx + 1}`,
          reached: Boolean(wp.reached)
        })).filter(wp => !isNaN(wp.lat) && !isNaN(wp.lon));

        const normalizedMission: Mission = {
          id: chosen.id,
          name: chosen.name,
          description: chosen.description,
          status: chosen.status,
          created_at: chosen.created_at,
          waypoints: normalizedWaypoints.length > 0 ? normalizedWaypoints : defaultMission.waypoints
        };

        actions.setActiveMission(normalizedMission);
        currentWpIndexRef.current = 0;
        if (normalizedMission.waypoints.length > 0) {
          setDroneState(prev => ({
            ...prev,
            lat: normalizedMission.waypoints[0].lat,
            lon: normalizedMission.waypoints[0].lon,
          }));
        }
      } else {
        actions.setActiveMission(defaultMission);
      }
    }).catch(() => {
      actions.setActiveMission(defaultMission);
    });
  }, [actions]);

  // Fetch tracks from backend database periodically
  useEffect(() => {
    const fetchTracks = () => {
      getTracks().then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setTracks(prev => {
            // merge with existing to retain simulated live micro-motion
            return data.map((d: any, idx) => {
              const existing = prev.find(p => p.id === (d.id || d.track_id));
              return {
                id: d.id || d.track_id || idx + 1,
                class_name: d.class_name || 'vehicle',
                lat: existing?.lat ?? d.last_lat ?? d.lat ?? 48.1350,
                lon: existing?.lon ?? d.last_lon ?? d.lon ?? 11.5820,
                speed: d.last_speed_mps ?? d.speed ?? 10.0,
                heading: d.last_heading_deg ?? d.heading ?? 90.0,
                status: d.status || 'confirmed',
                last_seen: new Date().toISOString()
              };
            });
          });
        }
      }).catch(() => {});
    };

    fetchTracks();
    const interval = setInterval(fetchTracks, 5000);
    return () => clearInterval(interval);
  }, []);

  // 10 Hz Real-Time Drone Autonomous Flight Interpolation along Waypoints
  useEffect(() => {
    const flightInterval = setInterval(() => {
      if (!activeMission || activeMission.status !== 'active') return;
      const wps = activeMission.waypoints;
      if (!wps || wps.length === 0) return;

      const targetWp = wps[currentWpIndexRef.current % wps.length];
      const targetLat = (targetWp as any).latitude ?? targetWp.lat;
      const targetLon = (targetWp as any).longitude ?? targetWp.lon;
      const targetAlt = (targetWp as any).altitude ?? targetWp.alt ?? 50.0;

      setDroneState(current => {
        const curLat = current.lat;
        const curLon = current.lon;

        const dist = getDistanceMeters(curLat, curLon, targetLat, targetLon);
        const heading = getBearing(curLat, curLon, targetLat, targetLon);

        // Reached waypoint threshold (8 meters)
        if (dist < 8.0) {
          // Mark waypoint reached
          const nextIndex = (currentWpIndexRef.current + 1) % wps.length;
          currentWpIndexRef.current = nextIndex;

          const updatedWaypoints = wps.map((wp, idx) => ({
            ...wp,
            reached: idx <= currentWpIndexRef.current
          }));

          actions.setActiveMission({
            ...activeMission,
            waypoints: updatedWaypoints
          });

          return {
            ...current,
            lat: targetLat,
            lon: targetLon,
            heading,
            alt: targetAlt,
            speed: 14.5,
            battery: Math.max(10, current.battery - 0.005),
            status: 'ACTIVE',
            timestamp: new Date().toISOString()
          };
        }

        // Move 1.45 meters towards target (equivalent to ~14.5 m/s at 100ms interval)
        const moveRatio = Math.min(1.0, 1.45 / dist);
        const newLat = curLat + (targetLat - curLat) * moveRatio;
        const newLon = curLon + (targetLon - curLon) * moveRatio;

        return {
          ...current,
          lat: newLat,
          lon: newLon,
          heading,
          alt: targetAlt,
          speed: 14.5,
          battery: Math.max(10, current.battery - 0.002),
          status: 'ACTIVE',
          timestamp: new Date().toISOString()
        };
      });
    }, 100);

    return () => clearInterval(flightInterval);
  }, [activeMission, actions]);

  // Subtle real-time motion for targets so they drive/walk dynamically
  useEffect(() => {
    const targetInterval = setInterval(() => {
      setTracks(prev =>
        prev.map(t => {
          let lat = (t as any).lat ?? (t as any).last_lat ?? 48.1348;
          let lon = (t as any).lon ?? (t as any).last_lon ?? 11.5815;
          let heading = (t as any).heading ?? (t as any).last_heading_deg ?? 90;
          let speed = (t as any).speed ?? (t as any).last_speed_mps ?? 10;

          if (t.id === 1 || t.class_name.toLowerCase() === 'car') {
            lon += 0.000015;
            if (lon > 11.5855) lon = 11.5795;
            heading = 88;
            speed = 9.7;
          } else if (t.id === 2 || t.class_name.toLowerCase() === 'person') {
            lat += 0.000004;
            if (lat > 48.1370) lat = 48.1345;
            heading = 10;
            speed = 1.2;
          } else if (t.id === 3 || t.class_name.toLowerCase() === 'truck') {
            lat -= 0.000012;
            if (lat < 48.1330) lat = 48.1365;
            heading = 180;
            speed = 7.9;
          }

          return {
            ...t,
            lat,
            lon,
            heading,
            speed,
            last_seen: new Date().toISOString()
          };
        })
      );
    }, 200);

    return () => clearInterval(targetInterval);
  }, []);

  const handleStatusChange = (status: MissionStatus) => {
    if (activeMission) {
      actions.setActiveMission({
        ...activeMission,
        status
      });
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-[#0a0f1a] overflow-hidden">
      {/* Top 60%: Map & Video / Status */}
      <div className="flex-1 flex flex-col lg:flex-row min-h-0 border-b border-gray-700">
        {/* Map: 60% with rotating drone aircraft & pinned targets */}
        <div className="w-full lg:w-3/5 h-full relative border-r border-gray-700 overflow-hidden">
          <GeoThreatMap
            droneState={droneState}
            detections={detections}
            tracks={tracks}
            mission={activeMission}
            selectedTrackId={selectedTrackId}
            onSelectTrack={actions.selectTrack}
          />
        </div>

        {/* Video & Status: 40% */}
        <div className="w-full lg:w-2/5 h-full flex flex-col overflow-hidden bg-gray-900/60 p-2 gap-2">
          <div className="flex-1 min-h-0 overflow-hidden relative">
            <VideoFeed
              detections={detections}
              tracks={tracks}
              droneState={droneState}
              selectedTrackId={selectedTrackId}
            />
          </div>
          <div className="h-20 shrink-0">
            <DroneStatus droneState={droneState} />
          </div>
        </div>
      </div>

      {/* Middle & Bottom: Target Table (60%) + Alerts (40%) + Mission Bar */}
      <div className="h-60 flex flex-col shrink-0 bg-[#0a0f1a]">
        <div className="flex-1 flex flex-col md:flex-row min-h-0 border-b border-gray-700">
          {/* Tracking Table (60%) */}
          <div className="w-full md:w-3/5 h-full border-r border-gray-700 overflow-hidden p-2">
            <TrackingTable
              tracks={tracks}
              selectedTrackId={selectedTrackId}
              onSelectTrack={actions.selectTrack}
            />
          </div>

          {/* Alert Timeline (40%) */}
          <div className="w-full md:w-2/5 h-full overflow-hidden p-2 bg-gray-900/50">
            <AlertTimeline alerts={alerts} />
          </div>
        </div>

        {/* Bottom Mission Progress Bar */}
        <div className="h-14 shrink-0 bg-[#111827] px-4 py-1.5 flex items-center">
          <MissionProgress mission={activeMission} onStatusChange={handleStatusChange} />
        </div>
      </div>
    </div>
  );
}
