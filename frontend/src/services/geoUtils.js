/**
 * Geographic and polyline utilities for calculating distances
 * and mapping HOS event mile markers to exact map coordinates.
 */

// Calculate great-circle distance in miles between two lat/lon coordinates
export function haversineDistanceMiles(lat1, lon1, lat2, lon2) {
  const R = 3958.8; // Earth's radius in miles
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Given a polyline [[lat, lon], ...] and a target mile marker,
 * finds the interpolated [lat, lon] coordinate along the polyline.
 */
export function getCoordinateAtMile(coordinates, targetMile, totalDistanceMiles = 0) {
  if (!coordinates || coordinates.length === 0) return null;
  if (coordinates.length === 1 || targetMile <= 0) return coordinates[0];

  // Precompute cumulative distances along the polyline
  let cumDistance = 0;
  const segmentDists = [];

  for (let i = 0; i < coordinates.length - 1; i++) {
    const [lat1, lon1] = coordinates[i];
    const [lat2, lon2] = coordinates[i + 1];
    const dist = haversineDistanceMiles(lat1, lon1, lat2, lon2);
    segmentDists.push(dist);
    cumDistance += dist;
  }

  // Scale factor in case OSRM total distance differs slightly from sum of coordinates
  const scale = (totalDistanceMiles > 0 && cumDistance > 0)
    ? cumDistance / totalDistanceMiles
    : 1;

  const targetDistPoly = targetMile * scale;

  if (targetDistPoly >= cumDistance) {
    return coordinates[coordinates.length - 1];
  }

  let runningDist = 0;
  for (let i = 0; i < segmentDists.length; i++) {
    const nextDist = runningDist + segmentDists[i];
    if (targetDistPoly <= nextDist && segmentDists[i] > 0) {
      const ratio = (targetDistPoly - runningDist) / segmentDists[i];
      const [lat1, lon1] = coordinates[i];
      const [lat2, lon2] = coordinates[i + 1];
      const lat = lat1 + (lat2 - lat1) * ratio;
      const lon = lon1 + (lon2 - lon1) * ratio;
      return [lat, lon];
    }
    runningDist = nextDist;
  }

  return coordinates[coordinates.length - 1];
}

/**
 * Extract clean, high-value planned HOS milestones from tripData
 * without cluttering the map with excessive icons.
 */
export function extractHOSMilestones(tripData) {
  if (!tripData) return [];

  const coordinates = tripData.coordinates || tripData.route?.coordinates || [];
  const totalMiles = tripData.route?.distance_miles || (tripData.distance_km ? tripData.distance_km * 0.621371 : 1000);
  const stops = tripData.stops || tripData.route?.stops || [];
  const events = tripData.master_events || tripData.events || [];

  const milestones = [];

  // 1. Origin Stop
  if (stops.length > 0 && stops[0].lat && stops[0].lng) {
    milestones.push({
      id: 'origin-stop',
      type: 'origin',
      title: 'ORIGIN / START',
      subtitle: stops[0].name || stops[0].address || 'Trip Start',
      address: stops[0].address,
      mile: 0,
      duration: '0 min',
      dutyStatus: 'ON DUTY',
      lat: stops[0].lat,
      lng: stops[0].lng,
      iconType: 'origin',
      badgeColor: '#3b82f6',
    });
  }

  // 2. Intermediate Stops & HOS Scheduled Events
  events.forEach((ev, idx) => {
    const activity = (ev.activity || '').toUpperCase();
    const status = (ev.status || '').toUpperCase();
    const mile = ev.start_mile || 0;

    // We only create milestone markers for non-driving operational stops
    if (activity === 'DRIVING' || activity === 'INITIAL_OFF_DUTY') {
      return;
    }

    let latLng = null;

    // If it corresponds to a named stop (Pickup / Dropoff), use exact stop coordinates
    if (activity === 'PICKUP' && stops.length > 1) {
      latLng = [stops[1].lat, stops[1].lng];
    } else if (activity === 'DROPOFF' && stops.length > 2) {
      latLng = [stops[stops.length - 1].lat, stops[stops.length - 1].lng];
    } else {
      // Calculate along route polyline
      latLng = getCoordinateAtMile(coordinates, mile, totalMiles);
    }

    if (!latLng) return;

    let iconType = 'break';
    let title = '30-MIN REST BREAK';
    let badgeColor = '#38bdf8';
    let category = 'break';

    if (activity === 'FUEL') {
      iconType = 'fuel';
      title = 'PLANNED FUEL STOP';
      badgeColor = '#f59e0b';
      category = 'fuel';
    } else if (activity === 'REST' || activity === 'RESTART' || status === 'SB') {
      iconType = 'rest';
      title = activity === 'RESTART' ? '34-HOUR CYCLE RESTART' : '10-HOUR SLEEPER BERTH';
      badgeColor = '#a855f7';
      category = 'hotel';
    } else if (activity === 'PICKUP') {
      iconType = 'pickup';
      title = 'FREIGHT PICKUP';
      badgeColor = '#f59e0b';
      category = 'pickup';
    } else if (activity === 'DROPOFF') {
      iconType = 'dropoff';
      title = 'FINAL FREIGHT DROPOFF';
      badgeColor = '#10b981';
      category = 'dropoff';
    }

    const durationMin = Math.round((ev.duration_hours || 0.5) * 60);
    const durationStr = durationMin >= 60 
      ? `${(durationMin / 60).toFixed(1)} hrs` 
      : `${durationMin} min`;

    const scheduledTime = ev.start_time 
      ? new Date(ev.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : `Hour ${((ev.start_mile || 0) / 55).toFixed(1)}`;

    milestones.push({
      id: ev.id || `milestone-${idx}`,
      type: iconType,
      category: category,
      title: title,
      subtitle: ev.location || `Route Mile ${mile.toFixed(1)}`,
      mile: mile,
      duration: durationStr,
      dutyStatus: status === 'D' ? 'DRIVING' : status === 'ON' ? 'ON DUTY' : status === 'SB' ? 'SLEEPER BERTH' : 'OFF DUTY',
      scheduledTime: scheduledTime,
      lat: latLng[0],
      lng: latLng[1],
      iconType: iconType,
      badgeColor: badgeColor,
      rawEvent: ev,
    });
  });

  return milestones;
}
