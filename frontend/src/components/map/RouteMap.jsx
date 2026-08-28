import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { createMilestoneIcon } from './MilestoneMarker';
import MilestonePopup from './MilestonePopup';
import { extractHOSMilestones } from '../../services/geoUtils';

function AutoFitBounds({ coordinates, milestones }) {
  const map = useMap();

  useEffect(() => {
    if (coordinates && coordinates.length > 0) {
      const bounds = L.latLngBounds(coordinates);
      milestones.forEach((m) => {
        if (m.lat && m.lng) {
          bounds.extend([m.lat, m.lng]);
        }
      });
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13, animate: true, duration: 1.0 });
    }
  }, [coordinates, milestones, map]);

  return null;
}

function PanToSelectedEvent({ selectedEvent, milestones }) {
  const map = useMap();

  useEffect(() => {
    if (!selectedEvent || !milestones) return;
    const target = milestones.find(
      (m) => m.id === selectedEvent.id || (m.rawEvent && m.rawEvent.id === selectedEvent.id)
    );
    if (target && target.lat && target.lng) {
      map.flyTo([target.lat, target.lng], 10, { animate: true, duration: 0.8 });
    }
  }, [selectedEvent, milestones, map]);

  return null;
}

export default function RouteMap({ routeData, selectedEvent }) {
  if (!routeData) return null;

  const coordinates = routeData.coordinates || routeData.route?.coordinates || [];
  const milestones = useMemo(() => extractHOSMilestones(routeData), [routeData]);

  if (coordinates.length === 0) return null;

  const center = coordinates[0] || [37.7749, -122.4194];

  return (
    <div className="map-wrapper">
      <div className="map-header-badge">
        <div className="map-badge-dot"></div>
        <span>Live Route Intelligence Map</span>
        <span className="badge-pill">{milestones.length} Scheduled HOS Milestones</span>
        {selectedEvent && (
          <span className="badge-selected-event">
            Active: <strong>{selectedEvent.activity}</strong> ({selectedEvent.status})
          </span>
        )}
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

          {/* Underlay glow route line */}
          <Polyline
            positions={coordinates}
            color="#38bdf8"
            weight={8}
            opacity={0.35}
            lineCap="round"
            lineJoin="round"
          />

          {/* Main sleek route line */}
          <Polyline
            positions={coordinates}
            color="#2563eb"
            weight={4.5}
            opacity={0.95}
            lineCap="round"
            lineJoin="round"
          />

          {/* Planned HOS Milestone Markers Only (No Clutter) */}
          {milestones.map((milestone) => {
            const icon = createMilestoneIcon(milestone.type);

            return (
              <Marker
                key={milestone.id}
                position={[milestone.lat, milestone.lng]}
                icon={icon}
              >
                <Popup className="premium-popup milestone-leaflet-popup" minWidth={280} maxWidth={340}>
                  <MilestonePopup milestone={milestone} />
                </Popup>
              </Marker>
            );
          })}

          <AutoFitBounds coordinates={coordinates} milestones={milestones} />
          <PanToSelectedEvent selectedEvent={selectedEvent} milestones={milestones} />
        </MapContainer>
      </div>
    </div>
  );
}
