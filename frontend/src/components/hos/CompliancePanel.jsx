import React from 'react';

export default function CompliancePanel({ validation = {} }) {
  const isValid = validation.is_valid !== false;
  const violations = validation.violations || [];

  const complianceRules = [
    { title: '11-Hour Driving Limit', desc: 'No more than 11 hours of driving between 10h rest periods (§ 395.3(a)(1))' },
    { title: '14-Hour Consecutive Duty Window', desc: 'No driving after the 14th consecutive hour on duty (§ 395.3(a)(2))' },
    { title: '30-Minute Break Requirement', desc: 'Break required after 8 cumulative hours of driving (§ 395.3(a)(3)(ii))' },
    { title: '10 Consecutive Hours Rest', desc: 'Mandatory 10-hour off-duty/sleeper before next work shift (§ 395.3(a)(1))' },
    { title: '70-Hour / 8-Day Cycle Ceiling', desc: 'Total on-duty time capped at 70 hours (§ 395.3(b)(2))' },
    { title: 'Mandatory Fuel Interval', desc: 'Fuel stop scheduled every ≤ 1,000 miles (30m ON-duty)' },
    { title: 'Timeline Continuity & Schema', desc: 'Strictly zero time gaps, zero overlaps, and 24.0h daily logs' },
  ];

  return (
    <div className={`compliance-panel-card ${isValid ? 'panel-compliant' : 'panel-violation'}`}>
      <div className="compliance-panel-header">
        <div className="header-text-group">
          <h4>FMCSA Property-Carrier HOS Compliance Verification</h4>
          <p className="header-sub">Automated audit engine validation for 49 CFR Part 395 regulations</p>
        </div>
        <div className={`compliance-banner ${isValid ? 'banner-pass' : 'banner-fail'}`}>
          <span className="banner-icon">{isValid ? '✓' : '⚠'}</span>
          <span>{isValid ? 'SCHEDULE COMPLIANT' : 'HOS VIOLATION DETECTED'}</span>
        </div>
      </div>

      {violations.length > 0 && (
        <div className="violations-alert-box">
          <h5 className="violations-title">Violations Identified by HOS Validator:</h5>
          <ul className="violations-list">
            {violations.map((v, idx) => (
              <li key={idx} className="violation-item">{v}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="rules-checklist-grid">
        {complianceRules.map((rule, idx) => (
          <div key={idx} className="rule-check-item">
            <div className={`check-icon-circle ${isValid ? 'circle-pass' : 'circle-check'}`}>
              <span>{isValid ? '✓' : '•'}</span>
            </div>
            <div className="rule-text-wrap">
              <span className="rule-title">{rule.title}</span>
              <span className="rule-desc">{rule.desc}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
