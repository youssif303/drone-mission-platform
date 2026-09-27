import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useDetections } from '../../hooks/useDetections';
import { useDroneTelemetry } from '../../hooks/useDroneTelemetry';
import { useAppStore } from '../../store/appStore';
import { TrackedObject, DroneState, GeoDetection, Mission } from '../../types';

// Fix Leaflet's default icon missing issue in bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom Rotating Drone Icon with Radar Ring
const createDroneIcon = (heading: number = 0) => new L.DivIcon({
  className: 'custom-drone-icon',
  html: `
    <div style="position: relative; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; transform: translate(-50%, -50%);">
      <!-- Radar scan ring -->
      <div style="position: absolute; width: 44px; height: 44px; border-radius: 50%; border: 1.5px dashed #10b981; opacity: 0.7;"></div>
      <div style="position: absolute; width: 28px; height: 28px; border-radius: 50%; background: rgba(16, 185, 129, 0.15);"></div>
      <!-- Aircraft Symbol -->
      <div style="transform: rotate(${heading}deg); transition: transform 0.2s linear; display: flex; align-items: center; justify-content: center;">
        <svg width="30" height="30" viewBox="0 0 24 24" fill="#10b981" stroke="#000000" stroke-width="1.5">
          <polygon points="12 2 2 22 12 18 22 22 12 2"></polygon>
        </svg>
      </div>
      <!-- Callsign Tag -->
      <div style="position: absolute; bottom: -12px; background: rgba(10, 15, 26, 0.9); color: #10b981; font-size: 9px; font-family: monospace; font-weight: bold; padding: 1px 4px; border-radius: 3px; border: 1px solid #10b981; white-space: nowrap; box-shadow: 0 0 6px rgba(0,0,0,0.8);">
        DRONE-01
      </div>
    </div>
  `,
  iconSize: [0, 0],
  iconAnchor: [0, 0]
});

// Target Marker Icon with clear labels and colors
const getTargetMarkerIcon = (className: string, id: number, isSelected: boolean) => {
  const colors: Record<string, string> = {
    car: '#f97316',      // orange
    person: '#ef4444',   // red
    truck: '#eab308',    // amber
    default: '#3b82f6',  // blue
  };
  const color = colors[className?.toLowerCase()] || colors.default;
  const border = isSelected ? '2px solid #10b981' : '1.5px solid white';
  const pulseHtml = isSelected 
    ? `<div style="position: absolute; width: 36px; height: 36px; border-radius: 50%; border: 2px solid #10b981; top: -14px; left: -14px; animation: ping 1.2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>`
    : '';

  return new L.DivIcon({
    className: 'custom-target-marker',
    html: `
      <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%); cursor: pointer;">
        ${pulseHtml}
        <div style="background-color: ${color}; color: white; font-weight: 800; font-size: 10px; font-family: monospace; padding: 2px 5px; border-radius: 4px; border: ${border}; box-shadow: 0 2px 8px rgba(0,0,0,0.9); white-space: nowrap; display: flex; align-items: center; gap: 3px;">
          <span>#${id}</span>
          <span>${className.toUpperCase()}</span>
        </div>
        <div style="width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid ${color};"></div>
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0]
  });
};

const waypointIcon = (num: number, reached: boolean = false) => new L.DivIcon({
  className: 'waypoint-icon',
  html: `
    <div style="background-color: ${reached ? '#10b981' : '#3b82f6'}; color: white; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; border: 2px solid white; box-shadow: 0 0 8px rgba(0,0,0,0.6); transform: translate(-50%, -50%);">
      ${reached ? '✓' : num}
    </div>
  `,
  iconSize: [0, 0],
  iconAnchor: [0, 0]
});

// Component to handle dynamic map centering on selection or drone
const MapController: React.FC<{ targetLat?: number; targetLon?: number; selectedLat?: number; selectedLon?: number }> = ({ targetLat, targetLon, selectedLat, selectedLon }) => {
  const map = useMap();

  useEffect(() => {
    if (typeof selectedLat === 'number' && typeof selectedLon === 'number' && !isNaN(selectedLat) && !isNaN(selectedLon)) {
      map.panTo([selectedLat, selectedLon], { animate: true, duration: 0.8 });
    }
  }, [selectedLat, selectedLon, map]);

  useEffect(() => {
    if (!selectedLat && typeof targetLat === 'number' && typeof targetLon === 'number' && !isNaN(targetLat) && !isNaN(targetLon)) {
      map.setView([targetLat, targetLon], map.getZoom(), { animate: false });
    }
  }, [targetLat, targetLon, selectedLat, map]);

  return null;
};

export interface GeoThreatMapProps {
  droneState?: DroneState | null;
  detections?: GeoDetection[];
  tracks?: TrackedObject[];
  mission?: Mission | null;
  selectedTrackId?: number | null;
  onSelectTrack?: (id: number) => void;
}

export const GeoThreatMap: React.FC<GeoThreatMapProps> = ({
  droneState: propDroneState,
  detections: propDetections,
  tracks: propTracks,
  mission: propMission,
  selectedTrackId: propSelectedTrackId,
  onSelectTrack,
}) => {
  const { detections: hookDetections } = useDetections();
  const { droneState: hookDroneState } = useDroneTelemetry();
  const storeMission = useAppStore(state => state.activeMission);
  const storeSelectedTrackId = useAppStore(state => state.selectedTrackId);

  const droneState = propDroneState || hookDroneState;
  const activeMission = propMission || storeMission;
  const selectedTrackId = propSelectedTrackId ?? storeSelectedTrackId;

  // Use tracks passed from Dashboard or fallback
  const displayTracks = (propTracks && propTracks.length > 0) ? propTracks : [
    { id: 1, class_name: 'car', lat: 48.1348, lon: 11.5815, speed: 35.0, heading: 85.0, status: 'confirmed', last_seen: new Date().toISOString() },
    { id: 2, class_name: 'person', lat: 48.1355, lon: 11.5825, speed: 4.2, heading: 12.0, status: 'confirmed', last_seen: new Date().toISOString() },
    { id: 3, class_name: 'truck', lat: 48.1360, lon: 11.5830, speed: 28.5, heading: 180.0, status: 'confirmed', last_seen: new Date().toISOString() },
  ];

  // Dynamic Flight trail of the drone
  const [flightTrail, setFlightTrail] = useState<[number, number][]>([
    [48.1340, 11.5800],
    [48.1345, 11.5810],
  ]);

  useEffect(() => {
    if (droneState?.lat && droneState?.lon) {
      setFlightTrail(prev => {
        const last = prev[prev.length - 1];
        if (!last || Math.abs(last[0] - droneState.lat) > 0.00005 || Math.abs(last[1] - droneState.lon) > 0.00005) {
          return [...prev.slice(-80), [droneState.lat, droneState.lon]];
        }
        return prev;
      });
    }
  }, [droneState?.lat, droneState?.lon]);

  const mapLat = droneState?.lat || 48.1351;
  const mapLon = droneState?.lon || 11.5820;

  // Find coords of selected track for camera auto-centering
  const selectedTrack = displayTracks.find(t => (t.id === selectedTrackId || (t as any).rawId === selectedTrackId));
  const selectedLat = selectedTrack ? ((selectedTrack as any).lat ?? (selectedTrack as any).last_lat) : undefined;
  const selectedLon = selectedTrack ? ((selectedTrack as any).lon ?? (selectedTrack as any).last_lon) : undefined;

  // Calculate Camera Sensor Ground Footprint (translucent FOV projection polygon ahead of drone)
  const fovHeadingRad = ((droneState?.heading || 0) * Math.PI) / 180;
  const fovDist = 0.0008; // ~80 meters ground projection length
  const fovWidth = 0.0006;
  const pFront = [
    mapLat + Math.cos(fovHeadingRad) * fovDist,
    mapLon + Math.sin(fovHeadingRad) * (fovDist * 1.5)
  ] as [number, number];
  const pLeft = [
    pFront[0] - Math.sin(fovHeadingRad) * fovWidth,
    pFront[1] + Math.cos(fovHeadingRad) * (fovWidth * 1.5)
  ] as [number, number];
  const pRight = [
    pFront[0] + Math.sin(fovHeadingRad) * fovWidth,
    pFront[1] - Math.cos(fovHeadingRad) * (fovWidth * 1.5)
  ] as [number, number];
  const fovPolygon: [number, number][] = [
    [mapLat, mapLon],
    pLeft,
    pRight,
    [mapLat, mapLon]
  ];

  return (
    <div className="w-full h-full relative z-0 min-h-[300px]">
      <MapContainer 
        center={[mapLat, mapLon]} 
        zoom={16} 
        style={{ height: '100%', width: '100%' }}
      >
        {/* Real ESRI High-Resolution Satellite Tiles */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="&copy; Esri &mdash; Satellite ISR"
        />

        <MapController 
          targetLat={mapLat} 
          targetLon={mapLon} 
          selectedLat={selectedLat} 
          selectedLon={selectedLon} 
        />

        {/* Drone Camera Sensor Ground Footprint (translucent green cone) */}
        <Polygon 
          positions={fovPolygon} 
          pathOptions={{ color: '#10b981', fillColor: '#10b981', fillOpacity: 0.12, weight: 1, dashArray: '3, 4' }} 
        />

        {/* Drone Flight Trail */}
        {flightTrail.length > 1 && (
          <Polyline positions={flightTrail} color="#10b981" weight={3} dashArray="4, 6" />
        )}

        {/* Mission Waypoints Path & Markers */}
        {activeMission?.waypoints && activeMission.waypoints.length > 0 && (
          <>
            <Polyline 
              positions={activeMission.waypoints.map(wp => [(wp as any).latitude ?? wp.lat, (wp as any).longitude ?? wp.lon])} 
              color="#3b82f6" 
              weight={2} 
              dashArray="6, 8" 
            />
            {activeMission.waypoints.map((wp, idx) => {
              const wLat = (wp as any).latitude ?? wp.lat;
              const wLon = (wp as any).longitude ?? wp.lon;
              const wAlt = (wp as any).altitude ?? wp.alt ?? 50;
              const reached = Boolean((wp as any).reached);
              if (!wLat || !wLon) return null;
              return (
                <Marker key={`wp-${idx}`} position={[wLat, wLon]} icon={waypointIcon(idx + 1, reached)}>
                  <Popup>
                    <div className="text-gray-900 font-sans text-xs">
                      <strong>Waypoint #{idx + 1}</strong><br/>
                      Altitude: {wAlt}m AGL<br/>
                      Status: {reached ? '✓ Reached' : 'En Route'}
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </>
        )}

        {/* TRACKED TARGET OBJECTS (Car, Person, Truck) */}
        {displayTracks.map(track => {
          const tLat = (track as any).lat ?? (track as any).last_lat;
          const tLon = (track as any).lon ?? (track as any).last_lon;
          const tSpeed = (track as any).speed ?? (track as any).last_speed_mps ?? 0;
          const isSelected = (track.id === selectedTrackId || (track as any).rawId === selectedTrackId);
          if (typeof tLat !== 'number' || typeof tLon !== 'number' || isNaN(tLat) || isNaN(tLon)) return null;

          return (
            <Marker
              key={`target-track-${track.id}`}
              position={[tLat, tLon]}
              icon={getTargetMarkerIcon(track.class_name, track.id, isSelected)}
              eventHandlers={{
                click: () => {
                  if (onSelectTrack) onSelectTrack(track.id);
                  else useAppStore.getState().actions.selectTrack(track.id);
                }
              }}
            >
              <Popup>
                <div className="text-gray-900 font-sans p-1">
                  <div className="font-bold text-sm text-green-700 flex items-center justify-between border-b pb-1">
                    <span>Target #{track.id}</span>
                    <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded uppercase font-mono">{track.class_name}</span>
                  </div>
                  <div className="text-xs mt-1 space-y-0.5 font-mono">
                    <div>GPS: {tLat.toFixed(5)}, {tLon.toFixed(5)}</div>
                    <div>Speed: {(tSpeed * 3.6).toFixed(1)} km/h</div>
                    <div>Status: <span className="text-green-600 font-bold uppercase">{track.status || 'CONFIRMED'}</span></div>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* LIVE DRONE AIRCRAFT MARKER */}
        {typeof droneState?.lat === 'number' && typeof droneState?.lon === 'number' && (
          <Marker 
            position={[droneState.lat, droneState.lon]} 
            icon={createDroneIcon(droneState.heading || 0)}
          >
            <Popup>
              <div className="text-gray-900 font-sans p-1">
                <div className="font-bold text-sm text-green-700 border-b pb-1 flex items-center gap-1">
                  <span>🚁 DRONE-01 (ACTIVE MISSION)</span>
                </div>
                <div className="text-xs mt-1.5 space-y-0.5 font-mono">
                  <div>Altitude: {(droneState.alt || 50).toFixed(1)}m AGL</div>
                  <div>Speed: {((droneState.speed || 15) * 3.6).toFixed(1)} km/h</div>
                  <div>Heading: {(droneState.heading || 0).toFixed(0)}°</div>
                  <div>Battery: {(droneState.battery || 95).toFixed(0)}%</div>
                  <div>Coordinates: {droneState.lat.toFixed(5)}, {droneState.lon.toFixed(5)}</div>
                </div>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Map Legend Overlay in corner */}
      <div className="absolute bottom-3 left-3 bg-black/80 backdrop-blur-sm border border-gray-700 p-2 rounded text-[11px] font-mono text-gray-300 z-[1000] flex flex-col gap-1 shadow-lg pointer-events-none">
        <div className="text-green-400 font-bold border-b border-gray-700 pb-0.5 uppercase tracking-wider text-[10px]">Tactical Map Legend</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block"></span> 🚁 Drone-01 Position</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-orange-500 inline-block"></span> #1 CAR</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span> #2 PERSON</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-yellow-500 inline-block"></span> #3 TRUCK</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span> Waypoints (1-{activeMission?.waypoints?.length || 4})</div>
      </div>
    </div>
  );
};

export default GeoThreatMap;
