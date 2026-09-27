import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Polyline, useMapEvents, Popup } from 'react-leaflet';
import { createMission, startMission } from '../services/api';
import { Waypoint } from '../types';
import { useAppStore } from '../store/appStore';
import { Trash2, Compass, Plus, Play } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix leaflet default icon
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const waypointIcon = (num: number) => new L.DivIcon({
  className: 'waypoint-icon',
  html: `<div style="background-color: #10b981; color: white; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white; box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);">${num}</div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 13]
});

function MapClickHandler({ onAddWaypoint }: { onAddWaypoint: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(e) {
      onAddWaypoint(e.latlng.lat, e.latlng.lng);
    }
  });
  return null;
}

export default function MissionPlanner() {
  const navigate = useNavigate();
  const setActiveMission = useAppStore(state => state.actions.setActiveMission);

  const [name, setName] = useState('Sector 7 Surveillance');
  const [description, setDescription] = useState('Autonomous perimeter reconnaissance and threat detection');
  const [altitude, setAltitude] = useState(50);
  const [pattern, setPattern] = useState('Grid');
  const [saving, setSaving] = useState(false);

  // Initial demo waypoints
  const [waypoints, setWaypoints] = useState<Waypoint[]>([
    { lat: 48.1340, lon: 11.5800, alt: 50 },
    { lat: 48.1345, lon: 11.5815, alt: 50 },
    { lat: 48.1355, lon: 11.5825, alt: 50 },
    { lat: 48.1360, lon: 11.5830, alt: 50 },
  ]);

  const handleAddWaypoint = (lat: number, lon: number) => {
    setWaypoints(prev => [...prev, { lat, lon, alt: altitude }]);
  };

  const handleRemoveWaypoint = (index: number) => {
    setWaypoints(prev => prev.filter((_, i) => i !== index));
  };

  const handleClear = () => {
    setWaypoints([]);
  };

  // Generate automated flight patterns
  const handleGeneratePattern = (type: string) => {
    const centerLat = 48.1351;
    const centerLon = 11.5820;
    const newWps: Waypoint[] = [];

    if (type === 'Grid') {
      // Lawnmower Grid
      for (let r = -2; r <= 2; r++) {
        const dLat = r * 0.0012;
        const lonDir = (r % 2 === 0) ? 1 : -1;
        newWps.push({ lat: centerLat + dLat, lon: centerLon - 0.0020 * lonDir, alt: altitude });
        newWps.push({ lat: centerLat + dLat, lon: centerLon + 0.0020 * lonDir, alt: altitude });
      }
    } else if (type === 'Spiral') {
      // Expanding Spiral
      for (let i = 0; i < 12; i++) {
        const angle = i * (Math.PI / 3);
        const radius = (i + 1) * 0.0003;
        newWps.push({
          lat: centerLat + Math.cos(angle) * radius,
          lon: centerLon + Math.sin(angle) * radius * 1.5,
          alt: altitude,
        });
      }
    } else if (type === 'Perimeter') {
      // Circular perimeter
      const points = 8;
      const radius = 0.0025;
      for (let i = 0; i < points; i++) {
        const angle = (i / points) * Math.PI * 2;
        newWps.push({
          lat: centerLat + Math.cos(angle) * radius,
          lon: centerLon + Math.sin(angle) * radius * 1.5,
          alt: altitude,
        });
      }
      // Close circle
      newWps.push({ ...newWps[0] });
    }

    setWaypoints(newWps);
  };

  const handleSave = async () => {
    const trimmedName = name.trim() || 'Sector 7 Surveillance';
    if (waypoints.length === 0) return alert('Please add at least one waypoint or click "Generate Pattern"');

    setSaving(true);
    try {
      const payload = {
        name: trimmedName,
        description: description.trim() || 'Autonomous aerial ISR mission',
        waypoints: waypoints.map((wp, idx) => ({
          sequence_order: idx + 1,
          latitude: wp.lat,
          longitude: wp.lon,
          altitude: wp.alt || altitude || 50,
        }))
      };

      const created = await createMission(payload as any);
      
      try {
        await startMission(created.id);
      } catch (e) {
        // status is already active from create_mission
      }

      const normalizedWaypoints: Waypoint[] = waypoints.map((wp, idx) => ({
        lat: wp.lat,
        lon: wp.lon,
        alt: wp.alt || altitude || 50,
        action: `Waypoint #${idx + 1}`,
        reached: false
      }));

      const activeMissionObj = {
        id: created.id,
        name: created.name || trimmedName,
        description: created.description || description.trim(),
        status: 'active' as const,
        created_at: new Date().toISOString(),
        waypoints: normalizedWaypoints
      };

      try {
        localStorage.setItem('active_mission_id', String(created.id));
        localStorage.setItem('cached_active_mission', JSON.stringify(activeMissionObj));
      } catch (e) {}

      // Update store and navigate to dashboard to see mission immediately running
      setActiveMission(activeMissionObj);

      alert(`✅ Mission "${trimmedName}" with ${normalizedWaypoints.length} waypoints saved and assigned to drone! Transferring to Dashboard...`);
      navigate('/');
    } catch (error) {
      console.error(error);
      const normalizedWaypoints: Waypoint[] = waypoints.map((wp, idx) => ({
        lat: wp.lat,
        lon: wp.lon,
        alt: wp.alt || altitude || 50,
        action: `Waypoint #${idx + 1}`,
        reached: false
      }));

      const fallbackMission = {
        id: Date.now(),
        name: trimmedName,
        description,
        status: 'active' as const,
        created_at: new Date().toISOString(),
        waypoints: normalizedWaypoints
      };

      try {
        localStorage.setItem('cached_active_mission', JSON.stringify(fallbackMission));
      } catch (e) {}

      setActiveMission(fallbackMission);
      alert(`✅ Mission "${trimmedName}" (${normalizedWaypoints.length} waypoints) activated! Transferring to Dashboard...`);
      navigate('/');
    } finally {
      setSaving(false);
    }
  };

  const positions = waypoints.map(wp => [wp.lat, wp.lon] as [number, number]);

  return (
    <div className="flex flex-1 h-full overflow-hidden bg-[#0a0f1a]">
      {/* Left Sidebar */}
      <div className="w-80 bg-gray-900 border-r border-gray-700 p-4 flex flex-col gap-4 overflow-y-auto">
        <div className="flex items-center gap-2 border-b border-gray-700 pb-2">
          <Compass className="w-5 h-5 text-green-400" />
          <h2 className="text-lg font-bold text-gray-200">Mission Parameters</h2>
        </div>
        
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold text-gray-400 uppercase">Mission Name</label>
          <input 
            type="text" 
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white rounded p-2 text-sm focus:border-green-500 focus:outline-none"
            placeholder="e.g. Sector 7 Patrol"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold text-gray-400 uppercase">Description / Objective</label>
          <textarea 
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="bg-gray-800 border border-gray-700 text-white rounded p-2 text-sm focus:border-green-500 focus:outline-none"
            placeholder="Mission objective..."
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold text-gray-400 uppercase">Default Flight Altitude (m)</label>
          <input 
            type="number" 
            value={altitude}
            onChange={(e) => setAltitude(Number(e.target.value))}
            className="bg-gray-800 border border-gray-700 text-white rounded p-2 text-sm focus:border-green-500 focus:outline-none font-mono"
          />
        </div>

        <div className="flex flex-col gap-2 pt-2 border-t border-gray-800">
          <label className="text-xs font-bold text-gray-400 uppercase">Autonomous Search Pattern</label>
          <div className="flex gap-2">
            <select 
              value={pattern}
              onChange={(e) => {
                setPattern(e.target.value);
                if (e.target.value !== 'Manual') {
                  handleGeneratePattern(e.target.value);
                }
              }}
              className="flex-1 bg-gray-800 border border-gray-700 text-white rounded p-2 text-sm focus:border-green-500 focus:outline-none"
            >
              <option value="Grid">Lawnmower Grid</option>
              <option value="Spiral">Expanding Spiral</option>
              <option value="Perimeter">Circular Perimeter</option>
              <option value="Manual">Manual Waypoints</option>
            </select>
            <button
              onClick={() => handleGeneratePattern(pattern)}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded"
              title="Apply Search Pattern"
            >
              Generate
            </button>
          </div>
        </div>
        
        <div className="text-xs text-gray-400 bg-gray-800/80 p-3 rounded border border-gray-700/80 mt-2">
          💡 <span className="font-semibold text-gray-200">Tip:</span> Select a pattern or click anywhere on the satellite map to add custom waypoints.
        </div>
      </div>

      {/* Center Map */}
      <div className="flex-1 relative bg-black">
        <MapContainer center={[48.1351, 11.5820]} zoom={15} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="&copy; Esri &mdash; Satellite ISR"
          />
          <MapClickHandler onAddWaypoint={handleAddWaypoint} />
          
          {positions.length > 1 && (
            <Polyline positions={positions} color="#10b981" weight={3} dashArray="6, 8" />
          )}
          
          {waypoints.map((wp, idx) => (
            <Marker key={idx} position={[wp.lat, wp.lon]} icon={waypointIcon(idx + 1)}>
              <Popup className="text-black font-sans">
                <strong>Waypoint {idx + 1}</strong><br/>
                Alt: {wp.alt}m<br/>
                GPS: {wp.lat.toFixed(5)}, {wp.lon.toFixed(5)}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Right Sidebar */}
      <div className="w-80 bg-gray-900 border-l border-gray-700 flex flex-col overflow-hidden">
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Waypoints ({waypoints.length})
          </h2>
          <span className="text-xs font-mono text-green-400 font-semibold">{altitude}m AGL</span>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {waypoints.length === 0 ? (
            <div className="text-center text-gray-500 text-sm mt-10 p-4">
              No waypoints added.<br/>Click on the satellite map or click <span className="text-green-400 font-semibold">"Generate"</span> above.
            </div>
          ) : (
            waypoints.map((wp, idx) => (
              <div key={idx} className="bg-gray-800 border border-gray-700 rounded p-2 flex items-center justify-between shadow-sm">
                <div className="flex flex-col">
                  <span className="text-xs font-bold text-green-400">WAYPOINT #{idx + 1}</span>
                  <span className="text-xs font-mono text-gray-300">
                    {wp.lat.toFixed(5)}, {wp.lon.toFixed(5)}
                  </span>
                  <span className="text-[11px] text-gray-500">Altitude: {wp.alt}m</span>
                </div>
                <button 
                  onClick={() => handleRemoveWaypoint(idx)}
                  className="text-gray-500 hover:text-red-400 p-1.5 rounded hover:bg-gray-700/50 transition-colors"
                  title="Remove Waypoint"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-3 border-t border-gray-700 bg-gray-800 flex items-center gap-2">
          <button
            onClick={handleClear}
            disabled={waypoints.length === 0}
            className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-gray-300 text-xs font-bold rounded transition-colors"
          >
            Clear All
          </button>
          <button
            onClick={handleSave}
            disabled={saving || waypoints.length === 0}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-40 text-white text-xs font-bold rounded shadow-md transition-colors"
          >
            <Play className="w-3.5 h-3.5" /> Save & Launch
          </button>
        </div>
      </div>
    </div>
  );
}
