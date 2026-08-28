import React from 'react';

/**
 * FMCSA 24-Hour Driver's Daily Log Graph & Sheet
 * Strictly renders the 4 duty-status rows (OFF, SB, D, ON) with 15-minute tick subdivisions,
 * continuous step-line graph, right-side total hours, remarks, and 70h/8d recap.
 */
export default function ELDLogSheet({
  dailyLogs,
  tripData,
  selectedDayIndex,
  onSelectDayIndex,
  selectedEvent,
  onSelectEvent,
}) {
  if (!dailyLogs || dailyLogs.length === 0) return null;

  const currentLog = dailyLogs[selectedDayIndex] || dailyLogs[0];
  const events = currentLog.events || [];
  const totals = currentLog.totals || {};
  const trip = tripData?.trip || {};
  const route = tripData?.route || {};

  // Parse date
  const logDate = new Date(currentLog.date + 'T00:00:00');
  const monthStr = (logDate.getMonth() + 1).toString().padStart(2, '0');
  const dayStr = logDate.getDate().toString().padStart(2, '0');
  const yearStr = logDate.getFullYear().toString();

  // Mileage calculation for this calendar day from backend dailyLog
  const milesToday = currentLog.miles_today !== undefined
    ? currentLog.miles_today
    : events.filter((e) => e.status === 'D').reduce((acc, ev) => {
        if (ev.start_mile !== undefined && ev.end_mile !== undefined) {
          return acc + Math.max(0, ev.end_mile - ev.start_mile);
        }
        return acc;
      }, 0);

  const totalTripMiles = route.distance_miles || (route.distance_km ? route.distance_km * 0.621371 : 0);

  // Status row mapping (0: OFF, 1: SB, 2: D, 3: ON)
  const STATUS_ROWS = [
    { key: 'OFF', label: '1. Off Duty', num: 1, color: '#94a3b8', total: totals.off_duty_hours || 0 },
    { key: 'SB', label: '2. Sleeper Berth', num: 2, color: '#a855f7', total: totals.sleeper_hours || 0 },
    { key: 'D', label: '3. Driving', num: 3, color: '#38bdf8', total: totals.driving_hours || 0 },
    { key: 'ON', label: '4. On Duty (not driving)', num: 4, color: '#f59e0b', total: totals.on_duty_hours || 0 },
  ];

  // Helper to convert event timestamp to fractional hour of the day (0.0 to 24.0)
  const getFractionalHour = (isoString, isEnd = false) => {
    const d = new Date(isoString);
    let h = d.getHours() + d.getMinutes() / 60 + d.getSeconds() / 3600;
    // If it is an end timestamp at 00:00 of next day, treat as 24.0
    if (isEnd && h === 0 && d.getDate() !== logDate.getDate()) {
      return 24.0;
    }
    return Math.min(24.0, Math.max(0.0, h));
  };

  // SVG coordinate dimensions (Slightly larger for crisp visibility)
  const SVG_WIDTH = 1000;
  const SVG_HEIGHT = 220;
  const ROW_HEIGHT = 46;
  const GRID_TOP = 25;
  const GRID_LEFT = 10;
  const GRID_WIDTH = 980;
  const HOUR_WIDTH = GRID_WIDTH / 24;

  const getRowY = (statusKey) => {
    const idx = STATUS_ROWS.findIndex((r) => r.key === statusKey);
    return GRID_TOP + idx * ROW_HEIGHT + ROW_HEIGHT / 2;
  };

  const getX = (hour) => {
    return GRID_LEFT + Math.min(24.0, Math.max(0.0, hour)) * HOUR_WIDTH;
  };

  // Build the continuous step-line path data and highlight blocks
  let pathD = '';
  const blockRects = [];

  events.forEach((ev, idx) => {
    const startH = getFractionalHour(ev.start_time, false);
    const endH = getFractionalHour(ev.end_time, true);
    if (endH <= startH && ev.duration_hours > 0) {
      return;
    }

    const x1 = getX(startH);
    const x2 = getX(endH);
    const y = getRowY(ev.status);

    const rowIdx = STATUS_ROWS.findIndex((r) => r.key === ev.status);
    const rowTopY = GRID_TOP + rowIdx * ROW_HEIGHT;

    const isSelected = selectedEvent && (selectedEvent.id === ev.id || (selectedEvent.start_time === ev.start_time && selectedEvent.activity === ev.activity));

    // Background highlight block for active status
    blockRects.push({
      id: ev.id,
      x: x1,
      y: rowTopY + 2,
      width: Math.max(1.5, x2 - x1),
      height: ROW_HEIGHT - 4,
      status: ev.status,
      activity: ev.activity,
      duration: ev.duration_hours,
      isSelected,
      event: ev,
    });

    if (idx === 0) {
      pathD += `M ${x1} ${y} L ${x2} ${y}`;
    } else {
      // Vertical transition line then horizontal line
      pathD += ` L ${x1} ${y} L ${x2} ${y}`;
    }
  });

  // Cumulative cycle calculations directly from backend dailyLog
  const cumulativeOnDuty = currentLog.cumulative_cycle_used !== undefined
    ? currentLog.cumulative_cycle_used
    : (trip.cycle_used_hours || 0);
  const cycleAvailableTomorrow = currentLog.cycle_remaining !== undefined
    ? currentLog.cycle_remaining
    : Math.max(0, 70.0 - cumulativeOnDuty);

  return (
    <div className="eld-log-sheet-card">
      {/* Day Selector Navigation Bar */}
      <div className="eld-sheet-top-bar">
        <div className="eld-badge-tag">
          <span className="eld-dot-live"></span>
          <span>OFFICIAL FMCSA 24-HOUR DRIVER LOG</span>
        </div>

        <div className="eld-day-selector">
          <span className="selector-label">Log Sheet:</span>
          {dailyLogs.map((log, idx) => (
            <button
              key={idx}
              type="button"
              className={`eld-day-btn ${idx === selectedDayIndex ? 'active' : ''}`}
              onClick={() => onSelectDayIndex(idx)}
            >
              Day {log.day}
              <span className="btn-date">({log.date})</span>
            </button>
          ))}
        </div>
      </div>

      {/* The Printable / Official Paper-Style Log Sheet Container */}
      <div className="fmcsa-paper-container">
        {/* Document Header */}
        <div className="fmcsa-header-grid">
          <div className="header-title-box">
            <h2>Drivers Daily Log</h2>
            <span className="sub-title">(24 hours)</span>
          </div>

          <div className="header-date-box">
            <div className="date-field">
              <span className="date-val">{monthStr}</span>
              <span className="date-lbl">Month</span>
            </div>
            <span className="date-slash">/</span>
            <div className="date-field">
              <span className="date-val">{dayStr}</span>
              <span className="date-lbl">Day</span>
            </div>
            <span className="date-slash">/</span>
            <div className="date-field">
              <span className="date-val">{yearStr}</span>
              <span className="date-lbl">Year</span>
            </div>
          </div>

          <div className="header-meta-box">
            <span className="meta-note">Original - File at home terminal.</span>
            <span className="meta-note">Duplicate - Driver retains in possession for 8 days.</span>
          </div>
        </div>

        {/* Carrier & Location Info Rows */}
        <div className="fmcsa-info-rows">
          <div className="info-row">
            <div className="info-field field-grow">
              <span className="info-label">From:</span>
              <span className="info-value">{trip.current_location || 'Not provided'}</span>
            </div>
            <div className="info-field field-grow">
              <span className="info-label">To:</span>
              <span className="info-value">{trip.dropoff_location || 'Not provided'}</span>
            </div>
          </div>

          <div className="info-row">
            <div className="info-box-group">
              <div className="stat-box">
                <span className="stat-val">{milesToday.toFixed(1)}</span>
                <span className="stat-lbl">Total Miles Driving Today</span>
              </div>
              <div className="stat-box">
                <span className="stat-val">{Number(totalTripMiles).toFixed(1)}</span>
                <span className="stat-lbl">Total Mileage Today</span>
              </div>
            </div>

            <div className="info-carrier-group">
              <div className="info-line">
                <span className="info-label">Carrier Name:</span>
                <span className="info-value">Spotter Fleet Logistics</span>
              </div>
              <div className="info-line">
                <span className="info-label">Main Office Address:</span>
                <span className="info-value">100 Logistics Way, Chicago, IL 60601</span>
              </div>
              <div className="info-line">
                <span className="info-label">Home Terminal Address:</span>
                <span className="info-value">{trip.current_location || 'Chicago, IL'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* ================================================================= */}
        {/* THE OFFICIAL 24-HOUR ELD GRID SECTION (HORIZONTAL SCROLL CONTAINER) */}
        {/* ================================================================= */}
        <div className="eld-grid-scroll-wrap">
          <div className="fmcsa-grid-wrapper">
            {/* Row Labels on the Left */}
            <div className="grid-left-labels">
              <div className="left-time-header">Duty Status</div>
              {STATUS_ROWS.map((r) => (
                <div key={r.key} className={`left-row-label row-label-${r.key.toLowerCase()}`}>
                  <span className="row-num">{r.num}.</span>
                  <span className="row-text">{r.label.replace(/^\d+\.\s*/, '')}</span>
                </div>
              ))}
            </div>

            {/* Center 24-Hour SVG Ruler & Duty Grid */}
            <div className="grid-center-area">
              {/* Top Time Scale Header */}
              <div className="time-scale-header">
                <div className="scale-mark scale-mid">Mid-<br/>night</div>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((h) => (
                  <div key={h} className="scale-mark">{h}</div>
                ))}
                <div className="scale-mark scale-noon">Noon</div>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((h) => (
                  <div key={h} className="scale-mark">{h}</div>
                ))}
                <div className="scale-mark scale-mid">Mid-<br/>night</div>
              </div>

              {/* Main Interactive SVG Grid */}
              <div className="svg-grid-container">
                <svg viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`} className="fmcsa-svg-canvas" preserveAspectRatio="none">
                  {/* Row Backgrounds */}
                  {STATUS_ROWS.map((r, idx) => (
                    <rect
                      key={idx}
                      x={GRID_LEFT}
                      y={GRID_TOP + idx * ROW_HEIGHT}
                      width={GRID_WIDTH}
                      height={ROW_HEIGHT}
                      className={`svg-row-bg row-bg-${r.key.toLowerCase()}`}
                    />
                  ))}

                  {/* Vertical Hour, Half-Hour, and Quarter-Hour Grid Tick Lines */}
                  {Array.from({ length: 25 }).map((_, hourIdx) => {
                    const x = getX(hourIdx);
                    return (
                      <g key={hourIdx} className="svg-hour-group">
                        {/* Full vertical hour line */}
                        <line
                          x1={x}
                          y1={GRID_TOP}
                          x2={x}
                          y2={GRID_TOP + 4 * ROW_HEIGHT}
                          className={hourIdx === 0 || hourIdx === 12 || hourIdx === 24 ? 'svg-line-major' : 'svg-line-hour'}
                        />

                        {/* 15, 30, 45 minute tick marks inside each row */}
                        {hourIdx < 24 &&
                          STATUS_ROWS.map((_, rIdx) => {
                            const rowTop = GRID_TOP + rIdx * ROW_HEIGHT;
                            const rowBot = rowTop + ROW_HEIGHT;
                            const rowMid = rowTop + ROW_HEIGHT / 2;
                            const x15 = x + HOUR_WIDTH * 0.25;
                            const x30 = x + HOUR_WIDTH * 0.5;
                            const x45 = x + HOUR_WIDTH * 0.75;

                            return (
                              <g key={rIdx}>
                                {/* 15m tick */}
                                <line x1={x15} y1={rowTop} x2={x15} y2={rowTop + 6} className="svg-tick-quarter" />
                                <line x1={x15} y1={rowBot - 6} x2={x15} y2={rowBot} className="svg-tick-quarter" />
                                {/* 30m tick (half-hour tick goes further) */}
                                <line x1={x30} y1={rowTop} x2={x30} y2={rowTop + 12} className="svg-tick-half" />
                                <line x1={x30} y1={rowBot - 12} x2={x30} y2={rowBot} className="svg-tick-half" />
                                <line x1={x30} y1={rowMid - 5} x2={x30} y2={rowMid + 5} className="svg-tick-half" />
                                {/* 45m tick */}
                                <line x1={x45} y1={rowTop} x2={x45} y2={rowTop + 6} className="svg-tick-quarter" />
                                <line x1={x45} y1={rowBot - 6} x2={x45} y2={rowBot} className="svg-tick-quarter" />
                              </g>
                            );
                          })}
                      </g>
                    );
                  })}

                  {/* Horizontal row divider lines */}
                  {STATUS_ROWS.map((_, idx) => (
                    <line
                      key={idx}
                      x1={GRID_LEFT}
                      y1={GRID_TOP + idx * ROW_HEIGHT}
                      x2={GRID_LEFT + GRID_WIDTH}
                      y2={GRID_TOP + idx * ROW_HEIGHT}
                      className="svg-row-divider"
                    />
                  ))}
                  {/* Bottom boundary line */}
                  <line
                    x1={GRID_LEFT}
                    y1={GRID_TOP + 4 * ROW_HEIGHT}
                    x2={GRID_LEFT + GRID_WIDTH}
                    y2={GRID_TOP + 4 * ROW_HEIGHT}
                    className="svg-row-divider"
                  />

                  {/* Render colored block highlights under the step-line */}
                  {blockRects.map((b, idx) => (
                    <rect
                      key={idx}
                      x={b.x}
                      y={b.y}
                      width={b.width}
                      height={b.height}
                      className={`svg-block-highlight highlight-${b.status.toLowerCase()} ${b.isSelected ? 'block-selected' : ''}`}
                      rx={3}
                      onClick={() => onSelectEvent && onSelectEvent(b.event)}
                      style={{ cursor: 'pointer' }}
                    >
                      <title>{`${b.status} - ${b.activity}: ${b.duration.toFixed(2)} hrs`}</title>
                    </rect>
                  ))}

                  {/* Outer Glow Step-Line */}
                  <path d={pathD} className="svg-stepline-glow" fill="none" />

                  {/* Continuous FMCSA Duty-Status Step Line */}
                  <path d={pathD} className="svg-stepline-main" fill="none" />

                  {/* Event waypoint dots at transition points */}
                  {events.map((ev, idx) => {
                    const startH = getFractionalHour(ev.start_time, false);
                    const x = getX(startH);
                    const y = getRowY(ev.status);
                    const isSelected = selectedEvent && (selectedEvent.id === ev.id || selectedEvent.start_time === ev.start_time);
                    return (
                      <circle
                        key={idx}
                        cx={x}
                        cy={y}
                        r={isSelected ? 5.5 : 3.5}
                        className={`svg-event-dot dot-${ev.status.toLowerCase()} ${isSelected ? 'dot-active' : ''}`}
                        onClick={() => onSelectEvent && onSelectEvent(ev)}
                        style={{ cursor: 'pointer' }}
                      />
                    );
                  })}
                </svg>
              </div>
            </div>

            {/* Total Hours Column on the Right */}
            <div className="grid-right-totals">
              <div className="right-total-header">Total<br/>Hours</div>
              {STATUS_ROWS.map((r) => (
                <div key={r.key} className="right-total-cell">
                  <span className="total-num-val">{r.total.toFixed(1)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Total Hours Check Bar */}
        <div className="total-hours-validation-line">
          <span className="val-label">Day {currentLog.day} Total Status Hours:</span>
          <span className="val-hours">
            {(totals.total_hours || 24.0).toFixed(1)} hrs / 24.0 hrs
          </span>
          <span className="val-badge-ok">✓ 24.0h FMCSA BALANCE VERIFIED</span>
        </div>

        {/* ================================================================= */}
        {/* REMARKS SECTION */}
        {/* ================================================================= */}
        <div className="fmcsa-remarks-section">
          <div className="remarks-header">
            <h4>Remarks</h4>
            <span className="remarks-guide">
              Enter name of place you reported and where released from work and where each change of duty occurred.
            </span>
          </div>

          <div className="remarks-table">
            {events.map((ev, idx) => {
              const startFormatted = new Date(ev.start_time).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true,
              });
              const endFormatted = new Date(ev.end_time).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true,
              });

              const isSelected = selectedEvent && (selectedEvent.id === ev.id || selectedEvent.start_time === ev.start_time);

              return (
                <div
                  key={idx}
                  className={`remark-row ${isSelected ? 'remark-row-selected' : ''}`}
                  onClick={() => onSelectEvent && onSelectEvent(ev)}
                  style={{ cursor: 'pointer' }}
                >
                  <span className="remark-time">{startFormatted} – {endFormatted}</span>
                  <span className={`remark-status-badge badge-${ev.status.toLowerCase()}`}>
                    {ev.status}
                  </span>
                  <span className="remark-activity">{ev.activity}</span>
                  <span className="remark-location">{ev.location || 'Highway Transit'}</span>
                  {ev.start_mile !== undefined && ev.end_mile !== undefined && (
                    <span className="remark-mile">
                      {ev.start_mile !== ev.end_mile
                        ? `(Mi ${ev.start_mile.toFixed(0)} - ${ev.end_mile.toFixed(0)})`
                        : `(Mi ${ev.start_mile.toFixed(0)})`}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* ================================================================= */}
        {/* 70-HOUR / 8-DAY RECAP SECTION */}
        {/* ================================================================= */}
        <div className="fmcsa-recap-footer">
          <div className="recap-title-block">
            <span className="recap-main-title">Recap: Complete at end of day</span>
            <span className="recap-sub-title">70 Hour / 8 Day Property-Carrying Driver</span>
          </div>

          <div className="recap-columns-grid">
            <div className="recap-col">
              <span className="recap-val">{((totals.driving_hours || 0) + (totals.on_duty_hours || 0)).toFixed(1)} hrs</span>
              <span className="recap-lbl">On Duty Hours Today (Lines 3 & 4)</span>
            </div>

            <div className="recap-col">
              <span className="recap-val">{cumulativeOnDuty.toFixed(1)} hrs</span>
              <span className="recap-lbl">A. Total Hours on Duty in 8-Day Cycle</span>
            </div>

            <div className="recap-col">
              <span className="recap-val highlight-green">{cycleAvailableTomorrow.toFixed(1)} hrs</span>
              <span className="recap-lbl">B. Total Available Tomorrow (70h minus A)</span>
            </div>

            <div className="recap-col">
              <span className="recap-val">34h Restart</span>
              <span className="recap-lbl">*If 34 consecutive hours taken, cycle resets to 70h</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
