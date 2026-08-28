import React from 'react';
import TripPlanner from './pages/TripPlanner';
import './App.css';

function App() {
  return (
    <div className="app-layout">
      {/* Top Global Navigation Bar */}
      <nav className="top-nav">
        <div className="nav-brand">
          <div className="brand-logo-gem">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="#c084fc" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <span className="brand-name">SPOTTER <span className="brand-accent">TMS</span></span>
          <span className="brand-tag">v2.4 ELD</span>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="main-content">
        <TripPlanner />
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Spotter TMS &copy; {new Date().getFullYear()} — Electronic Logging Device & Logistics Routing Engine</p>
      </footer>
    </div>
  );
}

export default App;

