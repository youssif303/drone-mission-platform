import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { GeoDetection } from '../types';

export function useDetections() {
  const { data, isConnected } = useWebSocket<any>('/ws/detections');
  const [detections, setDetections] = useState<GeoDetection[]>([
    {
      track_id: 1,
      class_name: 'car',
      confidence: 0.94,
      bbox: [450, 320, 520, 380],
      lat: 48.1348,
      lon: 11.5815,
      speed: 35.0,
      heading: 85.0,
      timestamp: new Date().toISOString(),
    },
    {
      track_id: 2,
      class_name: 'person',
      confidence: 0.88,
      bbox: [320, 240, 350, 290],
      lat: 48.1355,
      lon: 11.5825,
      speed: 4.2,
      heading: 12.0,
      timestamp: new Date().toISOString(),
    }
  ]);

  useEffect(() => {
    if (!data) return;

    let items: any[] = [];
    if (Array.isArray(data)) {
      items = data;
    } else if (data.detections && Array.isArray(data.detections)) {
      items = data.detections;
    } else if (typeof data === 'object') {
      items = [data];
    }

    const normalized: GeoDetection[] = items.map((item, idx) => {
      const lat = item.lat ?? item.latitude ?? 48.1351;
      const lon = item.lon ?? item.longitude ?? 11.5820;
      const track_id = item.track_id ?? item.id ?? (idx + 1);
      const class_name = item.class_name ?? 'vehicle';
      const confidence = item.confidence ?? 0.9;
      const speed = item.speed ?? item.speed_mps ?? 0;
      const heading = item.heading ?? item.heading_deg ?? 0;
      const timestamp = item.timestamp ? String(item.timestamp) : new Date().toISOString();
      const bbox = item.bbox ?? [100, 100, 150, 150];

      return {
        track_id: Number(track_id),
        class_name,
        confidence: Number(confidence),
        bbox,
        lat: Number(lat),
        lon: Number(lon),
        speed: Number(speed),
        heading: Number(heading),
        timestamp,
      } as GeoDetection;
    }).filter(d => !isNaN(d.lat) && !isNaN(d.lon));

    if (normalized.length > 0) {
      setDetections(prev => {
        const map = new Map(prev.map(d => [d.track_id, d]));
        for (const det of normalized) {
          map.set(det.track_id, det);
        }
        return Array.from(map.values()).slice(-20);
      });
    }
  }, [data]);

  return { detections, isConnected };
}
