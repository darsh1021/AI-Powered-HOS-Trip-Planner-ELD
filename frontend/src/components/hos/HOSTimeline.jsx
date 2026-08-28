import React from 'react';

export default function HOSTimeline({ events, selectedDay, onSelectEvent }) {
  if (!events || events.length === 0) {
    return (
      <div className="hos-timeline-container empty-timeline">
        <p>No HOS events scheduled.</p>
      </div>
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'D': return { label: 'D', name: 'DRIVE', class: 'status-d', color: '#38bdf8' };
      case 'ON': return { label: 'ON', name: 'ON DUTY', class: 'status-on', color: '#f59e0b' };
      case 'SB': return { label: 'SB', name: 'SLEEPER', class: 'status-sb', color: '#a855f7' };
      case 'OFF': return { label: 'OFF', name: 'OFF DUTY', class: 'status-off', color: '#94a3b8' };
      default: return { label: status, name: status, class: '', color: '#fff' };
    }
  };

  const formatTime = (isoString) => {
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const formatHoursMinutes = (hours) => {
    const totalMinutes = Math.round(hours * 60);
    const hrs = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    if (hrs === 0) return `${mins}m`;
    if (mins === 0) return `${hrs}h`;
    return `${hrs}h ${mins}m`;
  };

  return (
    <div className="hos-timeline-card">
      <div className="timeline-card-header">
        <div className="timeline-header-title">
          <h4>HOS Operational Timeline</h4>
          <span className="timeline-sub">
            {selectedDay ? `Day ${selectedDay.day} Schedule (${selectedDay.date})` : 'Full Trip Event Sequence'}
          </span>
        </div>

        {/* Legend for 4 Duty Statuses */}
        <div className="status-legend">
          <div className="legend-item"><span className="legend-dot status-d"></span><strong>D</strong> Driving</div>
          <div className="legend-item"><span className="legend-dot status-on"></span><strong>ON</strong> On-Duty</div>
          <div className="legend-item"><span className="legend-dot status-sb"></span><strong>SB</strong> Sleeper</div>
          <div className="legend-item"><span className="legend-dot status-off"></span><strong>OFF</strong> Off-Duty</div>
        </div>
      </div>

      {/* Proportional Duty-Status Bar */}
      <div className="status-timeline-bar">
        {events.map((ev, idx) => {
          const badge = getStatusBadge(ev.status);
          const flexRatio = Math.max(ev.duration_hours, 0.2);
          return (
            <div
              key={idx}
              className={`timeline-bar-segment ${badge.class}`}
              style={{ flex: flexRatio }}
              title={`${badge.name}: ${formatHoursMinutes(ev.duration_hours)} (${formatTime(ev.start_time)} - ${formatTime(ev.end_time)})`}
              onClick={() => onSelectEvent && onSelectEvent(ev)}
            >
              {ev.duration_hours >= 1.5 && (
                <span className="bar-segment-label">{badge.label}</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Sequential Event List */}
      <div className="event-stream">
        {events.map((ev, idx) => {
          const badge = getStatusBadge(ev.status);
          const timeStart = formatTime(ev.start_time);
          const timeEnd = formatTime(ev.end_time);
          const dateStr = formatDate(ev.start_time);

          return (
            <div
              key={idx}
              className={`event-stream-row ${badge.class}`}
              onClick={() => onSelectEvent && onSelectEvent(ev)}
            >
              <div className="event-time-col">
                <span className="time-primary">{timeStart} – {timeEnd}</span>
                <span className="time-date">{dateStr}</span>
              </div>

              <div className="event-marker-col">
                <div className={`status-pill ${badge.class}`}>
                  {badge.label}
                </div>
                {idx < events.length - 1 && <div className="event-connector-line"></div>}
              </div>

              <div className="event-info-col">
                <div className="event-title-row">
                  <span className="activity-name">{ev.activity}</span>
                  <span className="duration-tag">{formatHoursMinutes(ev.duration_hours)}</span>
                </div>
                <div className="event-location-row">
                  <span className="loc-text">{ev.location || 'En route segment'}</span>
                  {ev.start_mile !== undefined && ev.end_mile !== undefined && ev.start_mile !== ev.end_mile && (
                    <span className="mile-tag">Mi {ev.start_mile.toFixed(0)} → {ev.end_mile.toFixed(0)}</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
