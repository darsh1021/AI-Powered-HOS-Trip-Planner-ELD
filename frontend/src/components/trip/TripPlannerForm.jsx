import React, { useState } from 'react';

const PRESETS = [
  {
    name: 'US Cross-Country (Chi → Dal → LA)',
    current: 'Chicago, IL',
    pickup: 'Dallas, TX',
    dropoff: 'Los Angeles, CA',
    cycle: '24',
  },
  {
    name: 'East Coast Corridor (NY → Atl → Mia)',
    current: 'New York, NY',
    pickup: 'Atlanta, GA',
    dropoff: 'Miami, FL',
    cycle: '18',
  },
  {
    name: 'Heavy Cycle Test (Chi → Dal → LA, 66h)',
    current: 'Chicago, IL',
    pickup: 'Dallas, TX',
    dropoff: 'Los Angeles, CA',
    cycle: '66',
  },
];

export default function TripPlannerForm({ onSubmit, loading, loadingStage }) {
  const [formData, setFormData] = useState({
    current_location: 'Chicago, IL',
    pickup_location: 'Dallas, TX',
    dropoff_location: 'Los Angeles, CA',
    cycle_used_hours: '24',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handlePreset = (preset) => {
    setFormData({
      current_location: preset.current,
      pickup_location: preset.pickup,
      dropoff_location: preset.dropoff,
      cycle_used_hours: preset.cycle,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      cycle_used_hours: Number(formData.cycle_used_hours) || 0,
    });
  };

  return (
    <div className="trip-form-card">
      <div className="form-card-header">
        <div className="form-title-group">
          <h3>Trip Parameters & Dispatch</h3>
          <p className="form-subtitle">Enter route waypoints to calculate optimal trajectory & HOS compliance schedule</p>
        </div>
        <div className="preset-container">
          <span className="preset-label">Quick Presets:</span>
          <div className="preset-chips">
            {PRESETS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className="preset-chip"
                onClick={() => handlePreset(p)}
                disabled={loading}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="planner-form-grid">
        {/* Current Location (Origin) */}
        <div className="form-field-group">
          <label className="field-label">
            <span className="field-icon origin-icon">📍</span>
            <span>Current Location (Origin)</span>
          </label>
          <div className="input-wrapper">
            <input
              type="text"
              name="current_location"
              value={formData.current_location}
              onChange={handleChange}
              placeholder="e.g. Chicago, IL"
              required
              disabled={loading}
              className="modern-input"
            />
          </div>
        </div>

        {/* Pickup Location */}
        <div className="form-field-group">
          <label className="field-label">
            <span className="field-icon pickup-icon">📦</span>
            <span>Pickup Location</span>
          </label>
          <div className="input-wrapper">
            <input
              type="text"
              name="pickup_location"
              value={formData.pickup_location}
              onChange={handleChange}
              placeholder="e.g. Dallas, TX"
              required
              disabled={loading}
              className="modern-input"
            />
          </div>
        </div>

        {/* Dropoff Location */}
        <div className="form-field-group">
          <label className="field-label">
            <span className="field-icon dropoff-icon">🏁</span>
            <span>Dropoff Location</span>
          </label>
          <div className="input-wrapper">
            <input
              type="text"
              name="dropoff_location"
              value={formData.dropoff_location}
              onChange={handleChange}
              placeholder="e.g. Los Angeles, CA"
              required
              disabled={loading}
              className="modern-input"
            />
          </div>
        </div>

        {/* Cycle Used Hours */}
        <div className="form-field-group">
          <label className="field-label">
            <span className="field-icon cycle-icon">⏱️</span>
            <span>Cycle Used Hours</span>
          </label>
          <div className="input-wrapper">
            <input
              type="number"
              name="cycle_used_hours"
              min="0"
              max="70"
              step="0.5"
              value={formData.cycle_used_hours}
              onChange={handleChange}
              placeholder="e.g. 24"
              required
              disabled={loading}
              className="modern-input"
            />
            <span className="input-unit">hrs / 70</span>
          </div>
        </div>

        {/* Action Button & Staged Loading indicator */}
        <div className="form-actions">
          <button type="submit" className="plan-btn" disabled={loading}>
            {loading ? (
              <span className="btn-loading-state">
                <span className="spinner-ring"></span>
                <span>{loadingStage || 'Processing HOS Schedule...'}</span>
              </span>
            ) : (
              <span className="btn-normal-state">
                <span>⚡ Calculate & Plan Route</span>
              </span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
