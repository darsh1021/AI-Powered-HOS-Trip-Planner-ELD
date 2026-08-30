Video Explaination : https://www.loom.com/share/8549fd5254c8426c9a6eb849bad4f4c2
# 🚛 AI-Powered HOS Trip Planner & Smart ELD (Spotter TMS)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django REST Framework](https://img.shields.io/badge/Django_REST_Framework-3.14%2B-red.svg?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/React-18-cyan.svg?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-purple.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Leaflet](https://img.shields.io/badge/Leaflet-GIS-brightgreen.svg?logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![OpenStreetMap](https://img.shields.io/badge/OpenStreetMap-OSRM_%26_Overpass-black.svg?logo=openstreetmap&logoColor=white)](https://www.openstreetmap.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Spotter TMS & Smart ELD** is a commercial fleet dispatching and regulatory compliance intelligence platform. It automates multi-stop road routing, mathematical **FMCSA Hours of Service (HOS)** scheduling under **49 CFR Part 395**, interactive geospatial route intelligence, and generates **Official FMCSA 24-Hour ELD Daily Log Sheets** with precision SVG timeline rendering.

---

## 📌 Table of Contents
1. [Key Features](#-key-features)
2. [FMCSA Regulatory Compliance Engine](#-fmcsa-regulatory-compliance-engine)
3. [Architecture & Tech Stack](#-architecture--tech-stack)
4. [Project Directory Structure](#-project-directory-structure)
5. [Quick Start & Installation](#-quick-start--installation)
   - [Backend Setup (Django)](#1-backend-setup-python--django)
   - [Frontend Setup (React + Vite)](#2-frontend-setup-react--vite)
6. [API Endpoints & Payloads](#-api-endpoints--payloads)
7. [Progressive HOS Milestones & POI Discovery](#-progressive-hos-milestones--poi-discovery)
8. [ELD Log Sheet Specifications](#-official-fmcsa-24-hour-eld-log-sheet)
9. [Contributing & License](#-license)

---

## 🌟 Key Features

- **⚡ Automated Multi-Stop Road Routing**: Geocodes origin, pickup, and delivery destinations using Nominatim and calculates turn-by-turn highway telemetry via Project OSRM.
- **🛡️ Deterministic FMCSA HOS Engine**: Automatically schedules required rest breaks, 10-hour sleeper berth resets, 1,000-mile fuel stops, and 34-hour cycle restarts.
- **📊 Official FMCSA 24-Hour ELD Grid**: Renders the standard DOT 4-row step graph (`OFF`, `SB`, `D`, `ON`) with midnight-to-midnight multi-day segmentation.
- **🗺️ Clean Route Map with Progressive Milestones (KISS Principle)**: Displays only scheduled HOS events (Start 🟢, Pickup 📦, 30m Break ☕, Planned Fuel Stop ⛽, 10h Sleeper Berth 🛏️, Dropoff 🏁) to keep routes clean.
- **⛽ On-Demand Free POI Discovery**: Integrated with OpenStreetMap Overpass API to find real nearby truck stops (*Love's*, *Pilot Flying J*, *TA*) and motels (*Super 8*, *Motel 6*, *DOT Rest Areas*) within 10 miles of any scheduled stop.
- **⏱️ Live Duty Recaps & Countdown Clocks**: Tracks drive time remaining, shift window, 8h break due countdown, and 70-hour / 8-day rolling cycle limits.
- **💰 100% Free & Open-Source Geospatial Stack**: Zero dependencies on paid Google Maps APIs.

---

## ⚖️ FMCSA Regulatory Compliance Engine

The engine complies with **US Federal Motor Carrier Safety Administration (FMCSA) 49 CFR Part 395** rules for commercial motor vehicle property carriers:

| Regulation Rule | Constraint | Automated Engine Behavior |
| :--- | :--- | :--- |
| **11-Hour Driving Limit** | Max 11.0 hours driving per shift | Automatically forces a 10-hour consecutive rest when drive limit is reached. |
| **14-Hour Shift Window** | Max 14.0 consecutive hours from shift start | Halts driving once shift window elapses regardless of driving hours. |
| **30-Minute Rest Break** | Mandatory break after 8.0 driving hours | Injects a 30-minute `OFF DUTY` or `ON DUTY (Not Driving)` break at ~7.5 hours. |
| **10-Hour Sleeper Berth / Rest** | 10 consecutive hours off-duty/sleeper | Resets the 11h drive clock and 14h shift window to 0. |
| **70-Hour / 8-Day Cycle** | Max 70 on-duty hours in rolling 8 days | Prevents dispatch if cycle is exceeded; schedules a **34-hour cycle restart**. |
| **Commercial Fueling Intervals** | Fuel stop every ~1,000 miles | Injects a 30-minute `ON DUTY (Fueling)` event at planned highway mile markers. |

---

## 🏗️ Architecture & Tech Stack

```
[ React 18 / Vite Frontend ]  <====== REST JSON ======>  [ Django REST Framework Backend ]
       │                                                               │
       ├── Leaflet & OSM Tiles                                         ├── Nominatim Geocoding API
       ├── SVG 24h ELD Grid Canvas                                     ├── Project OSRM Routing Engine
       └── Overpass POI Client (Fuel & Hotels)                         └── HOS State Machine & Validator
```

### Frontend
- **Framework**: React 18 + Vite
- **Mapping & GIS**: Leaflet, React-Leaflet, OpenStreetMap
- **Styling**: Vanilla Modern CSS (Tailored HSL design system, Glassmorphism, Dark UI)
- **Icons & Typography**: Outfit, Inter, JetBrains Mono

### Backend
- **Framework**: Python 3.10+, Django 4.2+, Django REST Framework (DRF)
- **Routing & Geodesy**: Project OSRM (`router.project-osrm.org`), Nominatim OpenStreetMap, Haversine formula
- **CORS & Middleware**: `django-cors-headers`
- **Validation**: Strict deterministic state machine (`trips.services.hos`)

---

## 📂 Project Directory Structure

```
spotter-tms/
├── backend/
│   ├── config/                     # Django project settings and root URLs
│   ├── manage.py                   # Django management CLI
│   ├── requirements.txt            # Python dependencies
│   └── trips/                      # Core trip planning & HOS application
│       ├── services/
│       │   ├── geocode.py          # Nominatim geocoding service
│       │   ├── routing.py          # OSRM road geometry & leg calculator
│       │   ├── trip_planner.py     # Master orchestration service
│       │   └── hos/
│       │       ├── models.py       # Dataclasses: HOSEvent, DailyLog, RouteResult
│       │       ├── rules.py        # Configurable FMCSA HOS rule definitions
│       │       ├── scheduler.py    # Deterministic HOS state machine scheduler
│       │       ├── calculator.py   # Calendar-day event splitter & 24h totals
│       │       └── validator.py    # Multi-rule regulatory compliance auditor
│       ├── tests/                  # Unit and scenario test suite
│       ├── urls.py                 # API route definitions
│       └── views.py                # REST API views
│
└── frontend/
    ├── package.json                # Node dependencies & build scripts
    ├── vite.config.js              # Vite bundler configuration
    ├── index.html                  # HTML entry point
    └── src/
        ├── services/
        │   ├── tripApi.js          # Backend API client with typed errors
        │   ├── geoUtils.js         # Polyline interpolation & milestone extractor
        │   └── poiService.js       # Free Overpass OSM API client (Fuel & Hotels)
        ├── components/
        │   ├── map/
        │   │   ├── RouteMap.jsx        # Leaflet map with scheduled HOS milestone pins
        │   │   ├── MilestoneMarker.jsx # Custom SVG glowing pins (🟢, 📦, ☕, ⛽, 🛏️, 🏁)
        │   │   └── MilestonePopup.jsx  # Progressive popup with [Find Nearby Stations]
        │   ├── hos/
        │   │   ├── ELDLogSheet.jsx     # Official FMCSA 24-hour SVG grid log sheet
        │   │   ├── HOSTimeline.jsx     # Interactive event stream & timeline
        │   │   ├── DailyHOSSummary.jsx # Day selector tabs & 24-hour totals breakdown
        │   │   ├── CompliancePanel.jsx # Audit check results & violation indicators
        │   │   ├── HOSEventCard.jsx    # Modal dialog for inspecting event metadata
        │   │   └── HOSSummary.jsx      # Summary wrapper component
        │   └── trip/
        │       ├── TripPlannerForm.jsx # Dispatcher input form (Locations + Cycle Hours)
        │       ├── TripSummary.jsx     # Top metrics HUD (Miles, Duration, Days, Compliance)
        │       └── RouteItinerary.jsx  # Chronological route legs & physical stops
        ├── pages/
        │   ├── TripPlanner.jsx     # Master planning workspace page
        │   └── TripPlanner.css     # Glassmorphism dark theme stylesheet
        └── App.jsx                 # Top-level layout & navigation bar
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Git**

---

### 1. Backend Setup (Python & Django)

```bash
# Navigate to the backend directory
cd spotter-tms/backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the Django development server
python manage.py runserver
```

The backend server will start at `http://127.0.0.1:8000/`.

---

### 2. Frontend Setup (React + Vite)

```bash
# Open a new terminal and navigate to the frontend directory
cd spotter-tms/frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```

The frontend development server will start at `http://localhost:5173/`.

---

## 📡 API Endpoints & Payloads

### `POST /api/trips/plan/`
Calculates road geometry, deterministic HOS schedules, and daily ELD logs.

#### Request Body
```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Dallas, TX",
  "dropoff_location": "Los Angeles, CA",
  "cycle_used_hours": 24.0,
  "start_time": "2026-08-28T08:00:00Z"
}
```

#### Response Structure (Truncated Overview)
```json
{
  "trip": {
    "current_location": "Chicago, IL",
    "pickup_location": "Dallas, TX",
    "dropoff_location": "Los Angeles, CA",
    "cycle_used_hours": 24.0
  },
  "route": {
    "distance_miles": 2415.8,
    "distance_km": 3887.8,
    "duration_hours": 37.4,
    "coordinates": [[41.8781, -87.6298], [41.8765, -87.6321], "..."],
    "legs": [...]
  },
  "hos_summary": {
    "total_driving_hours": 37.4,
    "total_on_duty_hours": 4.0,
    "total_sleeper_hours": 30.0,
    "total_off_duty_hours": 2.0,
    "total_duty_hours": 41.4,
    "total_calendar_days": 4,
    "is_compliant": true
  },
  "master_events": [...],
  "daily_logs": [
    {
      "day": 1,
      "date": "2026-08-28",
      "totals": { "driving_hours": 10.5, "on_duty_hours": 1.5, "sleeper_hours": 10.0, "off_duty_hours": 2.0 },
      "events": [...]
    }
  ],
  "validation": {
    "is_compliant": true,
    "violations": [],
    "checks_passed": [
      "11-Hour Daily Driving Limit Validated",
      "14-Hour Shift Window Validated",
      "30-Minute Rest Break Validated",
      "70-Hour / 8-Day Cycle Rule Validated"
    ]
  }
}
```

---

## ⛽ Progressive HOS Milestones & POI Discovery

To prevent visual map clutter, our interface follows the **Progressive Disclosure Pattern (KISS)**:

```
                      ⛽ Planned Fuel (Mile 947)
                      │
[Start] ─────── [Pickup] ──────┼─────── [10h Sleeper 🛏] ─────── [Dropoff 🏁]
                               │
```

1. **Clean Route View**: Only the scheduled HOS milestones appear along the polyline.
2. **Interactive Milestone Card**: Clicking any pin (e.g. ⛽ Fuel at Mile 947) displays:
   - Milestone mile marker
   - Scheduled time and duration
   - Duty status (`ON DUTY (Fueling)`)
3. **On-Demand Free POI Fetching**:
   - Clicking **`[ ⛽ Find Nearby Truck Stops ]`** queries OpenStreetMap Overpass API within 10 miles of that exact coordinate.
   - Lists top real-world facilities (*Love's*, *Pilot Flying J*, *TravelCenters of America*) with distance, diesel availability, and truck parking flags.

---

## 📋 Official FMCSA 24-Hour ELD Log Sheet

The log sheet faithfully replicates the **standard paper and electronic logging device (ELD) daily grid**:

```
 00:00      04:00      08:00      12:00      16:00      20:00     24:00
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────┐
│1. OFF    │██████████│          │          │          │          │ 8.0 │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼─────┤
│2. SB     │          │          │          │          │██████████│ 4.0 │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼─────┤
│3. D      │          │          │██████████│██████████│          │ 9.5 │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼─────┤
│4. ON     │          │██████    │          │          │          │ 2.5 │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴─────┘
```

- **SVG Grid Canvas**: Automatically connects status transitions with vertical step lines.
- **Midnight Splitting**: Accurately divides continuous events crossing 23:59:59 into consecutive daily log entries.
- **Recap Table**: Computes daily driving, on-duty, off-duty, sleeper berth hours, and 70-hour rolling cycle remaining.

---

## 🧪 Running Tests

### Backend Unit & Scenario Tests
```bash
cd spotter-tms/backend
python manage.py test trips.tests
```

### Frontend Build Validation
```bash
cd spotter-tms/frontend
npm run build
```

---

## 📄 License
This project is open-source and licensed under the [MIT License](LICENSE).
