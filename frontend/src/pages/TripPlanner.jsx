import React, { useState, useEffect } from 'react';
import TripPlannerForm from '../components/trip/TripPlannerForm';
import TripSummary from '../components/trip/TripSummary';
import RouteItinerary from '../components/trip/RouteItinerary';
import RouteStatus from '../components/trip/RouteStatus';
import RouteMap from '../components/map/RouteMap';

import HOSTimeline from '../components/hos/HOSTimeline';
import HOSEventCard from '../components/hos/HOSEventCard';
import DailyHOSSummary from '../components/hos/DailyHOSSummary';
import CompliancePanel from '../components/hos/CompliancePanel';
import HOSSummary from '../components/hos/HOSSummary';

import { planTripApi, ApiErrorType } from '../services/tripApi';
import './TripPlanner.css';

export default function TripPlanner() {
  const [tripData, setTripData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [error, setError] = useState(null);
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Auto-plan default cross-country trip on mount so dispatcher workspace is immediately live
  useEffect(() => {
    handlePlanTrip({
      current_location: 'Chicago, IL',
      pickup_location: 'Dallas, TX',
      dropoff_location: 'Los Angeles, CA',
      cycle_used_hours: 24,
    });
  }, []);

  const handlePlanTrip = async (formValues) => {
    setLoading(true);
    setError(null);
    setSelectedDayIndex(0);
    setSelectedEvent(null);

    // Staged loading feedback
    setLoadingStage('● Geocoding locations & finding coordinates...');
    const t1 = setTimeout(() => setLoadingStage('● Calculating road route & geometry...'), 700);
    const t2 = setTimeout(() => setLoadingStage('● Building deterministic HOS schedule...'), 1400);
    const t3 = setTimeout(() => setLoadingStage('● Validating FMCSA 70h/8d compliance...'), 2100);

    try {
      const data = await planTripApi(formValues);
      setTripData(data);
    } catch (err) {
      setError({
        type: err.type || ApiErrorType.SERVER_ERROR,
        message: err.message || 'Failed to plan trip and schedule HOS.',
      });
    } finally {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      setLoading(false);
      setLoadingStage('');
    }
  };

  const currentDailyLog = tripData?.daily_logs?.[selectedDayIndex];
  const displayedEvents = currentDailyLog?.events || tripData?.master_events || [];

  return (
    <div className="trip-planner-page">
      {/* Top Hero / Header */}
      <header className="planner-header">
        <div className="header-badge">
          <span className="live-pulse"></span>
          <span>SPOTTER TMS INTELLIGENCE</span>
        </div>
        <h1 className="header-title">Dispatcher HOS Planning Workspace</h1>
        <p className="header-desc">
          Automated multi-stop geocoding, OSRM road telemetry, and FMCSA 70-hour / 8-day HOS compliance engine
        </p>
      </header>

      {/* Top Input Form */}
      <section className="planner-section">
        <TripPlannerForm
          onSubmit={handlePlanTrip}
          loading={loading}
          loadingStage={loadingStage}
        />
      </section>

      {/* Structured Error State Banners */}
      {error && (
        <div className={`error-banner banner-type-${error.type.toLowerCase()}`}>
          <span className="error-icon">
            {error.type === ApiErrorType.HOS_VIOLATION ? '🛡️' : '⚠️'}
          </span>
          <div className="error-text">
            <strong>
              {error.type === ApiErrorType.HOS_ERROR && 'HOS Planning Error: '}
              {error.type === ApiErrorType.ROUTE_ERROR && 'Routing & Location Error: '}
              {error.type === ApiErrorType.HOS_VIOLATION && 'HOS Regulatory Violation: '}
              {error.type === ApiErrorType.SERVER_ERROR && 'System Server Error: '}
              {error.type === ApiErrorType.NETWORK_ERROR && 'Network Connection Error: '}
            </strong>
            {error.message}
          </div>
        </div>
      )}

      {/* Results Workspace */}
      {tripData && (
        <section className="results-section">
          {/* 1. Trip Summary (2-Row Metrics) */}
          <TripSummary tripData={tripData} />

          {/* 2. Route Itinerary & Map Overview */}
          <div className="route-display-grid">
            <RouteItinerary
              tripData={tripData}
              onSelectEvent={(ev) => setSelectedEvent(ev)}
            />
            <div className="map-view-column">
              <RouteMap routeData={tripData} selectedEvent={selectedEvent} />
            </div>
          </div>

          {/* 3. Daily HOS Summary (Day Tabs + 24h Totals Breakdown) */}
          {tripData.daily_logs && tripData.daily_logs.length > 0 && (
            <DailyHOSSummary
              dailyLogs={tripData.daily_logs}
              selectedDayIndex={selectedDayIndex}
              onSelectDayIndex={(idx) => setSelectedDayIndex(idx)}
              cycleInitial={tripData.trip?.cycle_used_hours || 0}
            />
          )}

          {/* 4. Centerpiece: HOS Timeline */}
          <HOSTimeline
            events={displayedEvents}
            selectedDay={currentDailyLog}
            onSelectEvent={(ev) => setSelectedEvent(ev)}
          />

          {/* 5. Independent FMCSA Compliance Panel */}
          <CompliancePanel validation={tripData.validation} />

          {/* 6. Official FMCSA 24-Hour ELD Daily Log Sheet */}
          {tripData.daily_logs && tripData.daily_logs.length > 0 && (
            <HOSSummary
              dailyLogs={tripData.daily_logs}
              tripData={tripData}
              selectedDayIndex={selectedDayIndex}
              onSelectDayIndex={(idx) => setSelectedDayIndex(idx)}
              selectedEvent={selectedEvent}
              onSelectEvent={(ev) => setSelectedEvent(ev)}
            />
          )}
        </section>
      )}

      {/* Staged Loading Overlay / Card */}
      {loading && (
        <div className="staged-loading-modal-backdrop">
          <div className="staged-loading-card">
            <div className="staged-loading-header">
              <span className="spinner-ring large"></span>
              <div>
                <h3>CALCULATING TRIP</h3>
                <p className="loading-sub">Running road routing & HOS optimization engine...</p>
              </div>
            </div>
            <div className="loading-steps-list">
              <div className="loading-step-item done">
                <span className="step-icon">✓</span>
                <span>Locations geocoded</span>
              </div>
              <div className="loading-step-item done">
                <span className="step-icon">✓</span>
                <span>Route & turn-by-turn road geometry calculated</span>
              </div>
              <div className="loading-step-item in-progress">
                <span className="step-icon">●</span>
                <span>Building deterministic FMCSA HOS schedule</span>
              </div>
              <div className="loading-step-item pending">
                <span className="step-icon">○</span>
                <span>Validating 70h/8d compliance & continuity</span>
              </div>
              <div className="loading-step-item pending">
                <span className="step-icon">○</span>
                <span>Generating 24-hour ELD daily logs</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Event Detail Modal */}
      {selectedEvent && (
        <HOSEventCard
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </div>
  );
}
