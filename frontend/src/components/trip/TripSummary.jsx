import React from 'react';

export default function TripSummary({ tripData }) {
  if (!tripData) return null;

  const route = tripData.route || {};
  const hos = tripData.hos || tripData.hos_summary || {};
  const validation = tripData.validation || {};

  // Formatter for hours/minutes
  const formatHoursMinutes = (hours) => {
    if (hours === undefined || hours === null) return '0h 00m';
    const totalMinutes = Math.round(hours * 60);
    const hrs = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    return `${hrs}h ${mins.toString().padStart(2, '0')}m`;
  };

  const distanceMiles = route.distance_miles || (route.distance_km ? (route.distance_km * 0.621371).toFixed(1) : 0);
  const distanceKm = route.distance_km || 0;
  const driveTimeHours = hos.driving_hours || (route.duration_hours || 0);
  const tripDays = hos.trip_days || (tripData.daily_logs ? tripData.daily_logs.length : 1);

  const isCompliant = hos.compliant !== undefined ? hos.compliant : (validation.is_valid === true);

  return (
    <div className="trip-summary-section">
      {/* Primary KPI Row */}
      <div className="metrics-grid primary-metrics">
        {/* Total Distance */}
        <div className="metric-card metric-primary">
          <div className="metric-icon-wrap blue-glow">
            <span>🛣️</span>
          </div>
          <div className="metric-info">
            <span className="metric-label">Total Distance</span>
            <span className="metric-value">{Number(distanceMiles).toLocaleString()} <small>miles</small></span>
            <span className="metric-sub">({Number(distanceKm).toLocaleString()} km)</span>
          </div>
        </div>

        {/* Total Drive Time */}
        <div className="metric-card metric-accent">
          <div className="metric-icon-wrap amber-glow">
            <span>⏱️</span>
          </div>
          <div className="metric-info">
            <span className="metric-label">Drive Time</span>
            <span className="metric-value">{formatHoursMinutes(driveTimeHours)}</span>
            <span className="metric-sub">segmented road transit</span>
          </div>
        </div>

        {/* Trip Days */}
        <div className="metric-card metric-purple">
          <div className="metric-icon-wrap purple-glow">
            <span>📅</span>
          </div>
          <div className="metric-info">
            <span className="metric-label">Trip Schedule</span>
            <span className="metric-value">{tripDays} <small>{tripDays === 1 ? 'Day' : 'Days'}</small></span>
            <span className="metric-sub">multi-day daily logs</span>
          </div>
        </div>

        {/* HOS Compliance Status */}
        <div className={`metric-card ${isCompliant ? 'metric-success' : 'metric-danger'}`}>
          <div className={`metric-icon-wrap ${isCompliant ? 'green-glow' : 'red-glow'}`}>
            <span>{isCompliant ? '🛡️' : '⚠️'}</span>
          </div>
          <div className="metric-info">
            <span className="metric-label">HOS Status</span>
            <span className={`metric-value status-badge-text ${isCompliant ? 'text-compliant' : 'text-violation'}`}>
              {isCompliant ? 'COMPLIANT ✓' : 'VIOLATION ⚠'}
            </span>
            <span className="metric-sub">
              {isCompliant ? 'FMCSA 70h/8d verified' : `${validation.violations?.length || 1} rule violation(s)`}
            </span>
          </div>
        </div>
      </div>

      {/* Secondary HOS Cycle Metrics Row */}
      <div className="metrics-grid secondary-metrics">
        {/* Cycle Used */}
        <div className="metric-card metric-subcard">
          <div className="metric-info">
            <span className="metric-label">Initial Cycle Used</span>
            <span className="metric-value-sm">{hos.cycle_used_hours_initial ?? tripData.trip?.cycle_used_hours ?? 0}h</span>
            <span className="metric-sub">pre-trip accumulated</span>
          </div>
        </div>

        {/* Cycle Remaining */}
        <div className="metric-card metric-subcard">
          <div className="metric-info">
            <span className="metric-label">Cycle Remaining</span>
            <span className="metric-value-sm text-cyan">{hos.cycle_remaining_hours ?? 0}h <small>/ 70h</small></span>
            <span className="metric-sub">70-hour capacity left</span>
          </div>
        </div>

        {/* Driving Hours Total */}
        <div className="metric-card metric-subcard">
          <div className="metric-info">
            <span className="metric-label">Total Driving Time</span>
            <span className="metric-value-sm">{formatHoursMinutes(hos.driving_hours)}</span>
            <span className="metric-sub">{hos.driving_hours ? `${hos.driving_hours.toFixed(1)}h` : '0h'} in status D</span>
          </div>
        </div>

        {/* On Duty Not Driving */}
        <div className="metric-card metric-subcard">
          <div className="metric-info">
            <span className="metric-label">On-Duty Not Driving</span>
            <span className="metric-value-sm">{formatHoursMinutes(hos.on_duty_hours)}</span>
            <span className="metric-sub">Pickup, Dropoff, Fuel</span>
          </div>
        </div>
      </div>
    </div>
  );
}
