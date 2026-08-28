import React from 'react';
import L from 'leaflet';

/**
 * Creates custom high-contrast SVG leaflet DivIcons for planned HOS milestones.
 */
export function createMilestoneIcon(type, label = '') {
  let bgGradient = 'linear-gradient(135deg, #3b82f6, #1d4ed8)';
  let glowColor = 'rgba(59, 130, 246, 0.6)';
  let borderColor = '#60a5fa';
  let symbol = label || '●';

  if (type === 'fuel') {
    bgGradient = 'linear-gradient(135deg, #f59e0b, #d97706)';
    glowColor = 'rgba(245, 158, 11, 0.65)';
    borderColor = '#fbbf24';
    symbol = '⛽';
  } else if (type === 'rest') {
    bgGradient = 'linear-gradient(135deg, #a855f7, #7e22ce)';
    glowColor = 'rgba(168, 85, 247, 0.65)';
    borderColor = '#c084fc';
    symbol = '🛏️';
  } else if (type === 'break') {
    bgGradient = 'linear-gradient(135deg, #0ea5e9, #0284c7)';
    glowColor = 'rgba(14, 165, 233, 0.65)';
    borderColor = '#38bdf8';
    symbol = '☕';
  } else if (type === 'pickup') {
    bgGradient = 'linear-gradient(135deg, #f97316, #c2410c)';
    glowColor = 'rgba(249, 115, 22, 0.65)';
    borderColor = '#fdba74';
    symbol = '📦';
  } else if (type === 'dropoff') {
    bgGradient = 'linear-gradient(135deg, #10b981, #047857)';
    glowColor = 'rgba(16, 185, 129, 0.65)';
    borderColor = '#34d399';
    symbol = '🏁';
  } else if (type === 'origin') {
    bgGradient = 'linear-gradient(135deg, #3b82f6, #1d4ed8)';
    glowColor = 'rgba(59, 130, 246, 0.65)';
    borderColor = '#93c5fd';
    symbol = '🟢';
  }

  const isEmoji = symbol.length > 2 || /[\u{1F300}-\u{1F9FF}]/u.test(symbol);
  const fontSize = isEmoji ? '15px' : '12px';

  const html = `
    <div class="milestone-pin-wrapper" style="
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      background: ${bgGradient};
      border: 2px solid ${borderColor};
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      box-shadow: 0 0 16px ${glowColor}, 0 4px 10px rgba(0,0,0,0.6);
      cursor: pointer;
      transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
    ">
      <span style="
        transform: rotate(45deg);
        color: white;
        font-weight: 800;
        font-size: ${fontSize};
        line-height: 1;
        text-shadow: 0 1px 3px rgba(0,0,0,0.8);
      ">${symbol}</span>
      <div style="
        position: absolute;
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        bottom: -11px;
        left: 12px;
        opacity: 0.8;
        box-shadow: 0 0 8px ${borderColor};
      "></div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-milestone-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36],
  });
}
