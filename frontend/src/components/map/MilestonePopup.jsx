import React, { useState } from 'react';
import { fetchNearbyFuelStations, fetchNearbyHotelsAndRestAreas } from '../../services/poiService';

export default function MilestonePopup({ milestone, onSelectPOI }) {
  const [loading, setLoading] = useState(false);
  const [poiList, setPoiList] = useState(null);
  const [error, setError] = useState(null);

  const canSearchPOI = milestone.category === 'fuel' || milestone.category === 'hotel' || milestone.category === 'break';
  const isFuel = milestone.category === 'fuel';

  const handleSearchNearby = async () => {
    setLoading(true);
    setError(null);

    try {
      let results = [];
      if (isFuel) {
        results = await fetchNearbyFuelStations(milestone.lat, milestone.lng);
      } else {
        results = await fetchNearbyHotelsAndRestAreas(milestone.lat, milestone.lng);
      }
      setPoiList(results);
    } catch (err) {
      setError('Could not reach OpenStreetMap. Using fallback road stations.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="milestone-popup-card">
      {/* Header */}
      <div className={`milestone-card-header tag-${milestone.type}`}>
        <span className="milestone-header-icon">
          {milestone.type === 'fuel' && '⛽'}
          {milestone.type === 'rest' && '🛏️'}
          {milestone.type === 'break' && '☕'}
          {milestone.type === 'pickup' && '📦'}
          {milestone.type === 'dropoff' && '🏁'}
          {milestone.type === 'origin' && '🟢'}
        </span>
        <div className="milestone-header-text">
          <div className="milestone-title">{milestone.title}</div>
          <div className="milestone-sub">{milestone.subtitle}</div>
        </div>
      </div>

      {/* Structured Stats Grid */}
      <div className="milestone-stats-box">
        <div className="milestone-stat-row">
          <span className="stat-label">Planned Milestone:</span>
          <span className="stat-val highlight">Mile {milestone.mile?.toFixed(1)}</span>
        </div>
        <div className="milestone-stat-row">
          <span className="stat-label">Duration:</span>
          <span className="stat-val">{milestone.duration}</span>
        </div>
        <div className="milestone-stat-row">
          <span className="stat-label">Duty Status:</span>
          <span className={`stat-val status-badge status-${milestone.dutyStatus?.toLowerCase().replace(/\s+/g, '-')}`}>
            {milestone.dutyStatus}
          </span>
        </div>
        {milestone.scheduledTime && (
          <div className="milestone-stat-row">
            <span className="stat-label">Scheduled Time:</span>
            <span className="stat-val">{milestone.scheduledTime}</span>
          </div>
        )}
      </div>

      {/* Progressive POI Discovery Action */}
      {canSearchPOI && (
        <div className="milestone-poi-section">
          {!poiList && !loading && (
            <button
              className="btn-find-poi"
              onClick={handleSearchNearby}
              type="button"
            >
              <span>{isFuel ? '⛽' : '🛏️'}</span>
              <span>{isFuel ? 'Find Nearby Truck Stops' : 'Find Nearby Lodging & Rest Areas'}</span>
            </button>
          )}

          {loading && (
            <div className="poi-loading-state">
              <span className="poi-spinner"></span>
              <span>Querying OpenStreetMap network...</span>
            </div>
          )}

          {error && <div className="poi-error-msg">{error}</div>}

          {poiList && (
            <div className="poi-results-container">
              <div className="poi-results-header">
                <span>Real Nearby Facilities ({poiList.length})</span>
                <button
                  className="btn-poi-refresh"
                  onClick={handleSearchNearby}
                  title="Refresh"
                >
                  ↻
                </button>
              </div>

              <div className="poi-list">
                {poiList.map((poi) => (
                  <div key={poi.id} className="poi-item-card">
                    <div className="poi-item-main">
                      <div className="poi-item-name">{poi.name}</div>
                      <div className="poi-item-addr">{poi.address}</div>
                      <div className="poi-amenity-tags">
                        {poi.diesel && <span className="tag-amenity">Diesel</span>}
                        {poi.truckParking && <span className="tag-amenity tag-hgv">Truck Parking</span>}
                        {poi.food && <span className="tag-amenity">Food</span>}
                        {poi.isRestArea && <span className="tag-amenity tag-rest">Rest Area</span>}
                      </div>
                    </div>
                    <div className="poi-item-right">
                      <div className="poi-distance">{poi.distanceMiles} mi</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
