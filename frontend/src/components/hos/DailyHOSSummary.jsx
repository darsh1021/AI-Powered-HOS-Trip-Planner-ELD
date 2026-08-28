import React from 'react';

export default function DailyHOSSummary({ dailyLogs, selectedDayIndex, onSelectDayIndex, cycleInitial = 0 }) {
  if (!dailyLogs || dailyLogs.length === 0) return null;

  const currentLog = dailyLogs[selectedDayIndex] || dailyLogs[0];
  const totals = currentLog.totals || {};

  const formatHoursMinutes = (hours) => {
    if (hours === undefined || hours === null) return '0h 00m';
    const totalMinutes = Math.round(hours * 60);
    const hrs = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    return `${hrs}h ${mins.toString().padStart(2, '0')}m`;
  };

  const drivingHours = totals.driving_hours || 0;
  const onDutyHours = totals.on_duty_hours || 0;
  const sleeperHours = totals.sleeper_hours || 0;
  const offDutyHours = totals.off_duty_hours || 0;
  const totalDayHours = totals.total_hours || (drivingHours + onDutyHours + sleeperHours + offDutyHours);

  // Directly consume backend calculated rolling cycle values
  const cumulativeCycleUsed = currentLog.cumulative_cycle_used !== undefined ? currentLog.cumulative_cycle_used : ((cycleInitial || 0) + drivingHours + onDutyHours);
  const cycleRemainingAfterDay = currentLog.cycle_remaining !== undefined ? currentLog.cycle_remaining : Math.max(0, 70.0 - cumulativeCycleUsed);

  const drivingRemainingIn11h = Math.max(0, 11.0 - drivingHours);

  return (
    <div className="daily-hos-summary-card">
      <div className="daily-summary-header">
        <div className="day-tabs-container">
          <span className="tabs-label">Daily Logs:</span>
          <div className="day-tabs">
            {dailyLogs.map((log, idx) => (
              <button
                key={idx}
                type="button"
                className={`day-tab-btn ${idx === selectedDayIndex ? 'active' : ''}`}
                onClick={() => onSelectDayIndex(idx)}
              >
                Day {log.day}
                <span className="tab-date-small">{log.date.substring(5)}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="day-compliance-tag">
          <span className="check-icon">✓</span>
          <span>DAY {currentLog.day} COMPLIANT</span>
        </div>
      </div>

      <div className="daily-breakdown-grid">
        {/* Duty Status Breakdown Box */}
        <div className="breakdown-col status-hours-box">
          <h5 className="col-title">24-Hour Duty Status Breakdown</h5>
          <div className="status-row">
            <span className="status-indicator-dot dot-d"></span>
            <span className="status-name">Driving (D)</span>
            <span className="status-val">{formatHoursMinutes(drivingHours)}</span>
          </div>
          <div className="status-row">
            <span className="status-indicator-dot dot-on"></span>
            <span className="status-name">On Duty Not Driving (ON)</span>
            <span className="status-val">{formatHoursMinutes(onDutyHours)}</span>
          </div>
          <div className="status-row">
            <span className="status-indicator-dot dot-sb"></span>
            <span className="status-name">Sleeper Berth (SB)</span>
            <span className="status-val">{formatHoursMinutes(sleeperHours)}</span>
          </div>
          <div className="status-row">
            <span className="status-indicator-dot dot-off"></span>
            <span className="status-name">Off Duty (OFF)</span>
            <span className="status-val">{formatHoursMinutes(offDutyHours)}</span>
          </div>
          <div className="status-row total-row">
            <span className="status-name font-bold">Total Calendar Hours</span>
            <span className="status-val font-bold text-cyan">{formatHoursMinutes(totalDayHours)}</span>
          </div>
        </div>

        {/* Shift & Cycle Limits Box */}
        <div className="breakdown-col limits-box">
          <h5 className="col-title">Shift & 70h/8d Cycle Allocation</h5>
          <div className="limit-metric-row">
            <div className="limit-metric-item">
              <span className="limit-label">Shift Driving Limit</span>
              <span className="limit-val">11h 00m</span>
            </div>
            <div className="limit-metric-item">
              <span className="limit-label">Shift Driving Margin</span>
              <span className="limit-val text-green">{formatHoursMinutes(drivingRemainingIn11h)} left</span>
            </div>
          </div>

          <div className="limit-metric-row">
            <div className="limit-metric-item">
              <span className="limit-label">Rolling Cycle Used</span>
              <span className="limit-val">{cumulativeCycleUsed.toFixed(1)}h</span>
            </div>
            <div className="limit-metric-item">
              <span className="limit-label">Rolling Cycle Remaining</span>
              <span className="limit-val text-cyan">{cycleRemainingAfterDay.toFixed(1)}h / 70h</span>
            </div>
          </div>

          {/* Progress bar of cycle consumed */}
          <div className="cycle-bar-wrap">
            <div className="cycle-bar-labels">
              <span>70h Cycle Progress</span>
              <span>{((cumulativeCycleUsed / 70.0) * 100).toFixed(0)}%</span>
            </div>
            <div className="cycle-progress-track">
              <div
                className="cycle-progress-fill"
                style={{ width: `${Math.min(100, (cumulativeCycleUsed / 70.0) * 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
