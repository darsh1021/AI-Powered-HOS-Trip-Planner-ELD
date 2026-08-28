import React from 'react';

export default function RouteStatus({ tripData }) {
  if (!tripData) return null;

  const route = tripData.route || {};
  const validation = tripData.validation || {};
  const isCompliant = validation.is_valid !== false;

  return (
    <div className="route-status-badge-bar">
      <div className="status-pill-group">
        <span className="telemetry-pill">
          <span className="dot-live"></span>
          SYSTEM OPERATIONAL
        </span>
        <span className="telemetry-pill">
          {route.coordinates?.length || 0} GPS Waypoints
        </span>
        <span className={`telemetry-pill ${isCompliant ? 'pill-success' : 'pill-danger'}`}>
          {isCompliant ? 'FMCSA HOS Verified' : 'Compliance Warning'}
        </span>
      </div>
    </div>
  );
}
