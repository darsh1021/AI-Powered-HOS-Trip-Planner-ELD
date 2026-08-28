import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Custom modern SVG markers for Origin, Pickup, and Dropoff
const createCustomIcon = (type, label) => {
  let color = '#3b82f6'; // Blue for origin/start
  let bgGradient = 'linear-gradient(135deg, #3b82f6, #1d4ed8)';
  let glowColor = 'rgba(59, 130, 246, 0.6)';

  if (type === 'pickup') {
    color = '#f59e0b'; // Amber/Orange
    bgGradient = 'linear-gradient(135deg, #f59e0b, #d97706)';
    glowColor = 'rgba(245, 158, 11, 0.6)';
  } else if (type === 'dropoff') {
    color = '#10b981'; // Emerald Green
    bgGradient = 'linear-gradient(135deg, #10b981, #059669)';
    glowColor = 'rgba(16, 185, 129, 0.6)';
  }

  const html = `
    <div style="
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      background: ${bgGradient};
      border: 2px solid rgba(255, 255, 255, 0.95);
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      box-shadow: 0 0 16px ${glowColor}, 0 4px 10px rgba(0,0,0,0.5);
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    ">
      <span style="
        transform: rotate(45deg);
        color: white;
        font-weight: 800;
        font-size: 13px;
        font-family: 'Inter', sans-serif;
        text-shadow: 0 1px 2px rgba(0,0,0,0.6);
      ">${label}</span>
      <div style="
        position: absolute;
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        bottom: -12px;
        left: 12px;
        opacity: 0.7;
        box-shadow: 0 0 8px ${color};
        animation: pulsePin 2s infinite;
      "></div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-map-pin',
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36]
  });
};

// Component to dynamically fit route bounds into view
function AutoFitBounds({ coordinates, stops }) {
  const map = useMap();

  useEffect(() => {
    if (coordinates && coordinates.length > 0) {
      const bounds = L.latLngBounds(coordinates);
      stops.forEach(stop => {
        if (stop.lat && stop.lng) {
          bounds.extend([stop.lat, stop.lng]);
        }
      });
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13, animate: true, duration: 1.2 });
    }
  }, [coordinates, stops, map]);

  return null;
}

export default function MapView({ routeData }) {
  if (!routeData || !routeData.coordinates || routeData.coordinates.length === 0) {
    return null;
  }

  const { coordinates, stops } = routeData;
  const center = coordinates[0] || [37.7749, -122.4194];

  const getStopType = (index, total) => {
    if (index === 0) return { type: 'origin', label: '1', name: 'Origin / Start' };
    if (index === total - 1) return { type: 'dropoff', label: String(total), name: 'Final Dropoff' };
    return { type: 'pickup', label: String(index + 1), name: `Stop ${index + 1}` };
  };

  return (
    <div className="map-wrapper">
      <div className="map-header-badge">
        <div className="map-badge-dot"></div>
        <span>Live Route Intelligence Map</span>
        <span className="badge-pill">{coordinates.length} waypoints</span>
      </div>

      <div className="map-container-inner">
        <MapContainer
          center={center}
          zoom={5}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%', borderRadius: '16px' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Underlay glow shadow line */}
          <Polyline
            positions={coordinates}
            color="#38bdf8"
            weight={8}
            opacity={0.35}
            lineCap="round"
            lineJoin="round"
          />

          {/* Main sleek route polyline */}
          <Polyline
            positions={coordinates}
            color="#2563eb"
            weight={4.5}
            opacity={0.95}
            lineCap="round"
            lineJoin="round"
            dashArray={null}
          />

          {/* Markers for stops */}
          {stops.map((stop, idx) => {
            const meta = getStopType(idx, stops.length);
            const icon = createCustomIcon(meta.type, meta.label);

            return (
              <Marker key={idx} position={[stop.lat, stop.lng]} icon={icon}>
                <Popup className="premium-popup">
                  <div className="popup-content">
                    <div className={`popup-header tag-${meta.type}`}>
                      {stop.name || meta.name}
                    </div>
                    <div className="popup-address">{stop.address}</div>
                    <div className="popup-coords">
                      {stop.lat?.toFixed(4)}, {stop.lng?.toFixed(4)}
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          <AutoFitBounds coordinates={coordinates} stops={stops} />
        </MapContainer>
      </div>
    </div>
  );
}

