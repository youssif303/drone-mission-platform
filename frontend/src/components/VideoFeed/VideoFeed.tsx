import React, { useEffect, useRef, useState } from 'react';
import { TrackedObject, DroneState, GeoDetection } from '../../types';
import { Eye, Crosshair, ZoomIn, ShieldAlert } from 'lucide-react';

export interface VideoFeedProps {
  detections?: GeoDetection[];
  tracks?: TrackedObject[];
  droneState?: DroneState | null;
  selectedTrackId?: number | null;
}

export const VideoFeed: React.FC<VideoFeedProps> = ({
  tracks = [],
  droneState,
  selectedTrackId,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [fps, setFps] = useState(15);
  const [isThermal, setIsThermal] = useState(false);
  const [zoom, setZoom] = useState(2);

  // Targets to render on camera
  const displayTracks = tracks.length > 0 ? tracks : [
    { id: 1, class_name: 'car', speed: 9.7, heading: 85, lat: 48.1348, lon: 11.5815 },
    { id: 2, class_name: 'person', speed: 1.2, heading: 12, lat: 48.1355, lon: 11.5825 },
    { id: 3, class_name: 'truck', speed: 7.9, heading: 180, lat: 48.1360, lon: 11.5830 },
  ];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let t = 0;

    const render = () => {
      t += 0.03;
      const w = canvas.width;
      const h = canvas.height;

      // 1. Background Aerial View Simulation (Simulating ground imagery through sensor)
      if (isThermal) {
        // FLIR White-Hot / Black-Hot Thermal Mode
        ctx.fillStyle = '#080c14';
        ctx.fillRect(0, 0, w, h);

        // Thermal road grid
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 14;
        ctx.beginPath();
        ctx.moveTo(0, h * 0.45);
        ctx.lineTo(w, h * 0.45);
        ctx.moveTo(w * 0.55, 0);
        ctx.lineTo(w * 0.55, h);
        ctx.stroke();
      } else {
        // High-Resolution Daylight EO Color Mode
        ctx.fillStyle = '#1e293b'; // Road asphalt
        ctx.fillRect(0, 0, w, h);

        // Ground features (roads, buildings, foliage)
        ctx.fillStyle = '#0f172a'; // building rooftop
        ctx.fillRect(30, 20, 160, 100);
        ctx.fillRect(w - 180, h - 130, 150, 110);

        // Park lawn
        ctx.fillStyle = '#143823';
        ctx.fillRect(20, h - 140, 180, 120);

        // Main asphalt avenues
        ctx.fillStyle = '#334155';
        ctx.fillRect(0, h * 0.42, w, 65); // East-West Avenue
        ctx.fillRect(w * 0.52, 0, 65, h); // North-South Street

        // Road dashed line markings
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 2;
        ctx.setLineDash([12, 10]);
        ctx.beginPath();
        ctx.moveTo(0, h * 0.42 + 32);
        ctx.lineTo(w, h * 0.42 + 32);
        ctx.moveTo(w * 0.52 + 32, 0);
        ctx.lineTo(w * 0.52 + 32, h);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // 2. Center Crosshairs & Optical Horizon Lines
      const cx = w / 2;
      const cy = h / 2;
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 1.5;

      // Optical reticle crosshair
      ctx.beginPath();
      ctx.moveTo(cx - 30, cy);
      ctx.lineTo(cx - 8, cy);
      ctx.moveTo(cx + 8, cy);
      ctx.lineTo(cx + 30, cy);
      ctx.moveTo(cx, cy - 30);
      ctx.lineTo(cx, cy - 8);
      ctx.moveTo(cx, cy + 8);
      ctx.lineTo(cx, cy + 30);
      ctx.stroke();

      // Pitch angle ladder marks
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
      ctx.strokeRect(cx - 40, cy - 40, 80, 80);

      // 3. Render Real Detected Target Objects in Camera FOV
      displayTracks.forEach((track, idx) => {
        const raw = track as any;
        const id = raw.id || idx + 1;
        const className = String(raw.class_name || 'TARGET').toUpperCase();
        const isLocked = (id === selectedTrackId);

        // Screen position calculation based on object offset
        let bx = 0;
        let by = 0;
        let bw = 0;
        let bh = 0;
        let targetColor = '#f97316';

        if (className.includes('CAR')) {
          // Car moving along East-West avenue
          const offset = ((t * 40 + idx * 120) % (w + 100)) - 50;
          bx = offset;
          by = h * 0.42 + 16;
          bw = 58;
          bh = 32;
          targetColor = '#f97316';
        } else if (className.includes('PERSON')) {
          // Person walking on sidewalk
          const offset = ((t * 12 + idx * 80) % (h + 80)) - 40;
          bx = w * 0.52 - 25;
          by = offset;
          bw = 24;
          bh = 42;
          targetColor = '#ef4444';
        } else if (className.includes('TRUCK')) {
          // Truck moving along North-South street
          const offset = (h - ((t * 30 + idx * 150) % (h + 100))) - 20;
          bx = w * 0.52 + 12;
          by = offset;
          bw = 42;
          bh = 75;
          targetColor = '#eab308';
        }

        // Draw Target Thermal / Physical Body inside box
        if (isThermal) {
          ctx.fillStyle = '#ffffff'; // Hot thermal signature
          ctx.shadowColor = '#ffffff';
          ctx.shadowBlur = 8;
          ctx.fillRect(bx + 4, by + 4, bw - 8, bh - 8);
          ctx.shadowBlur = 0;
        }

        // AI Bounding Box
        ctx.strokeStyle = isLocked ? '#10b981' : targetColor;
        ctx.lineWidth = isLocked ? 2.5 : 1.8;
        ctx.strokeRect(bx, by, bw, bh);

        // Corner tick marks
        const cl = 8;
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.5;
        // Top-left
        ctx.beginPath();
        ctx.moveTo(bx, by + cl);
        ctx.lineTo(bx, by);
        ctx.lineTo(bx + cl, by);
        // Bottom-right
        ctx.moveTo(bx + bw, by + bh - cl);
        ctx.lineTo(bx + bw, by + bh);
        ctx.lineTo(bx + bw - cl, by + bh);
        ctx.stroke();

        // Target Tag Header
        ctx.fillStyle = isLocked ? '#10b981' : targetColor;
        ctx.fillRect(bx, by - 16, Math.max(bw, 75), 16);
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 9px monospace';
        ctx.fillText(`#${id} ${className}`, bx + 3, by - 4);

        // Distance Rangefinder text under box
        const dist = (45 + idx * 8).toFixed(1);
        ctx.fillStyle = '#94a3b8';
        ctx.font = '9px monospace';
        ctx.fillText(`DIST: ${dist}m`, bx, by + bh + 12);

        // If target locked by user click: draw tactical tracking brackets
        if (isLocked) {
          ctx.strokeStyle = '#10b981';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(bx + bw / 2, by + bh / 2, 45, 0, Math.PI * 2);
          ctx.stroke();

          ctx.fillStyle = '#10b981';
          ctx.font = 'bold 11px monospace';
          ctx.fillText(`[LOCKED TARGET #${id} ${className}]`, cx - 80, cy - 65);
        }
      });

      // 4. Tactical OSD (On-Screen Display) Header
      ctx.fillStyle = '#10b981';
      ctx.font = '11px monospace';
      ctx.fillText(`CAM-01 [${isThermal ? 'FLIR THERMAL IR' : 'EO 4K DAYLIGHT'}]`, 14, 22);
      ctx.fillText(`ZOOM: ${zoom}.0x | PITCH: -45° | ALT: ${(droneState?.alt || 50).toFixed(0)}m AGL`, 14, 38);

      const latStr = (droneState?.lat || 48.1351).toFixed(5);
      const lonStr = (droneState?.lon || 11.5820).toFixed(5);
      ctx.fillText(`SENS: ${latStr}N, ${lonStr}E`, 14, 54);

      // Top right status
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(`TRACKING: ${displayTracks.length} OBJECTS`, w - 150, 22);
      ctx.fillText(`GIMBAL: STABILIZED`, w - 150, 38);

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [displayTracks, isThermal, zoom, droneState, selectedTrackId]);

  return (
    <div className="relative w-full h-full bg-[#030712] border border-gray-700 rounded-lg overflow-hidden flex items-center justify-center min-h-0">
      <canvas 
        ref={canvasRef} 
        width={640} 
        height={360} 
        className="w-full h-full object-contain"
      />
      
      {/* Sensor Control Overlays (Top Right) */}
      <div className="absolute top-2 right-2 flex items-center gap-1.5 z-10">
        <button
          onClick={() => setIsThermal(!isThermal)}
          className={`px-2 py-1 rounded text-[11px] font-mono font-bold border transition-colors flex items-center gap-1 ${
            isThermal 
              ? 'bg-amber-500 text-black border-amber-400' 
              : 'bg-black/70 text-gray-300 border-gray-700 hover:text-white'
          }`}
          title="Toggle Thermal IR / Daylight Camera"
        >
          <Eye className="w-3 h-3" />
          {isThermal ? 'THERMAL IR' : 'DAY EO'}
        </button>

        <button
          onClick={() => setZoom(z => (z === 4 ? 1 : z + 1))}
          className="px-2 py-1 bg-black/70 hover:bg-black/90 text-green-400 border border-gray-700 rounded text-[11px] font-mono font-bold flex items-center gap-1"
          title="Cycle Optical Zoom"
        >
          <ZoomIn className="w-3 h-3" />
          {zoom}x
        </button>

        <div className="bg-black/80 px-2 py-1 rounded text-xs font-mono text-green-400 border border-gray-700">
          {fps} FPS
        </div>
      </div>

      {/* Target Lock Banner when selected */}
      {selectedTrackId && (
        <div className="absolute bottom-2 left-2 bg-black/80 border border-green-500/80 px-2.5 py-1 rounded text-[11px] font-mono text-green-400 flex items-center gap-1.5 shadow-lg">
          <Crosshair className="w-3.5 h-3.5 text-green-400 animate-spin" />
          <span>AUTONOMOUS OPTICAL TRACK LOCK: #{selectedTrackId}</span>
        </div>
      )}
    </div>
  );
};

export default VideoFeed;
