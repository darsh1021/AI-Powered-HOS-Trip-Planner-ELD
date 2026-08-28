import React from 'react';

export default function RouteItinerary({ tripData, onSelectEvent }) {
  if (!tripData) return null;

  const masterEvents = tripData.master_events || [];
  const stops = tripData.route?.stops || [];
  const initialCycle = tripData.trip?.cycle_used_hours || 0;

  // Filter significant itinerary milestones (Origin, Pickup, Dropoff, Fuel, 10h Rest)
  const itineraryMilestones = [];

  // 1. Origin Milestone
  itineraryMilestones.push({
    type: 'ORIGIN',
    title: 'CURRENT ORIGIN',
    name: stops[0]?.address || 'Start Location',
    subtext: `Starting cycle: ${initialCycle.toFixed(1)}h used`,
    timeText: masterEvents[0] ? new Date(masterEvents[0].start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '08:00 AM',
    badge: 'START',
    badgeClass: 'badge-origin',
    icon: '📍',
  });

  // 2. Intermediate events (Pickups, Fuel stops, 10h Rest, Dropoff)
  masterEvents.forEach((ev, idx) => {
    const startTimeStr = new Date(ev.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const dateStr = new Date(ev.start_time).toLocaleDateString([], { month: 'short', day: 'numeric' });

    if (ev.activity === 'PICKUP') {
      itineraryMilestones.push({
        type: 'PICKUP',
        title: 'PICKUP APPOINTMENT',
        name: ev.location || 'Pickup Location',
        subtext: `+${ev.duration_hours.toFixed(1)}h ON DUTY (Resets 30m break clock)`,
        timeText: `${dateStr} · ${startTimeStr}`,
        badge: 'PICKUP',
        badgeClass: 'badge-pickup',
        icon: '📦',
        event: ev,
      });
    } else if (ev.activity === 'FUEL') {
      itineraryMilestones.push({
        type: 'FUEL',
        title: 'MANDATORY FUEL STOP',
        name: ev.location || `Fuel Stop @ Mile ${ev.start_mile}`,
        subtext: `+${ev.duration_hours * 60}m ON DUTY (Satisfies break requirement)`,
        timeText: `${dateStr} · ${startTimeStr}`,
        badge: 'FUEL',
        badgeClass: 'badge-fuel',
        icon: '⛽',
        event: ev,
      });
    } else if (ev.activity === 'REST' && ev.duration_hours >= 8.0) {
      itineraryMilestones.push({
        type: 'REST',
        title: '10-HOUR MANDATORY SLEEPER REST',
        name: ev.location || `Rest Area @ Mile ${ev.start_mile}`,
        subtext: `${ev.duration_hours.toFixed(1)}h SLEEPER BERTH (Resets 11h driving & 14h window)`,
        timeText: `${dateStr} · ${startTimeStr}`,
        badge: '10h REST',
        badgeClass: 'badge-rest',
        icon: '🛏️',
        event: ev,
      });
    } else if (ev.activity === 'RESTART') {
      itineraryMilestones.push({
        type: 'RESTART',
        title: '34-HOUR 70h CYCLE RESTART',
        name: ev.location || `34-Hour Restart Area`,
        subtext: `34.0h OFF DUTY (Fully resets 70-hour / 8-day cycle)`,
        timeText: `${dateStr} · ${startTimeStr}`,
        badge: '34h RESTART',
        badgeClass: 'badge-restart',
        icon: '🔄',
        event: ev,
      });
    } else if (ev.activity === 'DROPOFF') {
      itineraryMilestones.push({
        type: 'DROPOFF',
        title: 'FINAL DESTINATION (DROPOFF)',
        name: ev.location || 'Final Dropoff Destination',
        subtext: `+${ev.duration_hours.toFixed(1)}h ON DUTY (Trip Completed)`,
        timeText: `${dateStr} · ${startTimeStr}`,
        badge: 'DROPOFF',
        badgeClass: 'badge-dropoff',
        icon: '🏁',
        event: ev,
      });
    }
  });

  return (
    <div className="stops-timeline-card">
      <div className="card-heading">
        <div className="card-title-wrap">
          <h4>Operational Itinerary & HOS Stops</h4>
          <p className="card-subtitle">Waypoint stops, mandatory fueling, and qualifying rest checkpoints</p>
        </div>
        <span className="stops-count">{itineraryMilestones.length} Milestones</span>
      </div>

      <div className="timeline-list">
        {itineraryMilestones.map((item, idx) => (
          <div
            key={idx}
            className={`timeline-item ${item.event ? 'timeline-clickable' : ''}`}
            onClick={() => item.event && onSelectEvent && onSelectEvent(item.event)}
          >
            <div className={`timeline-marker ${item.badgeClass}`}>
              <span>{item.icon}</span>
            </div>
            <div className="timeline-details">
              <div className="timeline-header-row">
                <span className="timeline-stop-type">{item.title}</span>
                <span className="timeline-timestamp">{item.timeText}</span>
              </div>
              <div className="timeline-stop-name">{item.name}</div>
              <div className="timeline-stop-sub">{item.subtext}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
