import React from 'react';

export default function HOSEventCard({ event, onClose }) {
  if (!event) return null;

  const getStatusLabel = (status) => {
    switch (status) {
      case 'D': return 'DRIVING';
      case 'ON': return 'ON DUTY (NOT DRIVING)';
      case 'SB': return 'SLEEPER BERTH';
      case 'OFF': return 'OFF DUTY';
      default: return status;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'D': return 'tag-d';
      case 'ON': return 'tag-on';
      case 'SB': return 'tag-sb';
      case 'OFF': return 'tag-off';
      default: return '';
    }
  };

  const startFormatted = new Date(event.start_time).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const endFormatted = new Date(event.end_time).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const formatHoursMinutes = (hours) => {
    const totalMinutes = Math.round(hours * 60);
    const hrs = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    return `${hrs}h ${mins.toString().padStart(2, '0')}m`;
  };

  return (
    <div className="event-modal-overlay" onClick={onClose}>
      <div className="event-detail-card" onClick={(e) => e.stopPropagation()}>
        <div className="event-card-top">
          <span className={`status-badge ${getStatusClass(event.status)}`}>
            {getStatusLabel(event.status)}
          </span>
          <button type="button" className="close-btn" onClick={onClose}>✕</button>
        </div>

        <h3 className="event-activity-title">{event.activity}</h3>
        <p className="event-location-text">{event.location || 'Route Segment'}</p>

        <div className="event-details-grid">
          <div className="detail-item">
            <span className="detail-label">Start Time</span>
            <span className="detail-val">{startFormatted}</span>
          </div>

          <div className="detail-item">
            <span className="detail-label">End Time</span>
            <span className="detail-val">{endFormatted}</span>
          </div>

          <div className="detail-item">
            <span className="detail-label">Duration</span>
            <span className="detail-val highlight-val">{formatHoursMinutes(event.duration_hours)} ({event.duration_hours.toFixed(2)}h)</span>
          </div>

          <div className="detail-item">
            <span className="detail-label">Route Odometer</span>
            <span className="detail-val">
              {event.start_mile !== undefined && event.end_mile !== undefined && event.start_mile !== event.end_mile
                ? `Mile ${event.start_mile.toFixed(1)} → ${event.end_mile.toFixed(1)}`
                : `Mile ${event.start_mile?.toFixed(1) || 0.0}`}
            </span>
          </div>
        </div>

        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div className="event-metadata-box">
            <span className="metadata-title">Operational Telemetry:</span>
            {event.metadata.speed_mph && (
              <span className="metadata-badge">Avg Speed: {event.metadata.speed_mph} mph</span>
            )}
          </div>
        )}

        <div className="event-card-actions">
          <button type="button" className="action-btn-secondary" onClick={onClose}>Close Details</button>
        </div>
      </div>
    </div>
  );
}
