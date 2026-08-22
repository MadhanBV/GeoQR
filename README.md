# GeoQR – Secure Anti-Proxy Event Attendance System 🛡️📍

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg)](https://flask.palletsprojects.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-amber.svg)](https://firebase.google.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-22%20Passed-green.svg)](#running-automated-tests)

GeoQR is a production-grade, web-based event attendance system engineered for universities, colleges, and conferences to **completely eliminate proxy attendance (fake check-ins)**.

Students scan a dynamic QR code projected on the organizer's screen using their **mobile phone camera or browser—no mobile app download required**.

---

## 🔒 Anti-Proxy Multi-Layer Security Architecture

GeoQR eliminates proxy check-ins using a **5-layer validation pipeline**:

```
                         ┌─────────────────────────────────┐
                         │   Host Screen / Smartboard      │
                         │ Dynamic QR Code (Refreshes 25s) │
                         └────────────────┬────────────────┘
                                          │ Scans with phone camera
                                          ▼
                         ┌─────────────────────────────────┐
                         │   Student Mobile Browser UI     │
                         │   Auto-Acquires Device GPS      │
                         └────────────────┬────────────────┘
                                          │ Submits Attendance
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GeoQR Flask Backend Engine                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 1. Cryptographic HMAC Token Check  ➔ Validates signature & age (<= 25s)         │
│ 2. Event Match & Active State      ➔ Confirms event is open for attendance      │
│ 3. Duplicate Prevention Query      ➔ Verifies Student ID hasn't already checked │
│ 4. Server-Side Haversine Geofence  ➔ Computes exact spherical distance in meters│
│ 5. Atomic Firebase Commit          ➔ Records verified attendance in Firestore   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Mathematical Geofencing: Haversine Formula

To prevent spoofing flat-plane calculations, GeoQR uses the **Haversine formula** to measure great-circle distance over Earth's curved spherical surface:

$$\begin{aligned}
a &= \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right) \\
c &= 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right) \\
d &= R \cdot c \quad \text{where } R = 6,371,000\text{ meters}
\end{aligned}$$

- **$\phi_1, \phi_2$**: Latitude of organizer and student (in radians)
- **$\Delta \phi, \Delta \lambda$**: Difference in latitude and longitude
- **$d$**: Actual physical distance in meters

---

## 📁 Clean Architecture Directory Structure

```
GeoQR/
├── app.py                      # Flask Application Factory & Route Registration
├── config.py                   # Centralized Configuration & Environment Loading
├── requirements.txt            # Python Dependencies
├── .env                        # Local Environment Secrets
├── .env.example                # Example Environment Variables
├── firebase/
│   ├── firebase_config.py      # Dual-Mode Firestore Client (Live + In-Memory Emulator)
│   └── serviceAccountKey.json  # Google Cloud Firebase Private Key
├── models/
│   ├── event.py                # Event Entity & Serializers
│   └── attendance.py           # Attendance Record Entity & Serializers
├── services/
│   ├── event_service.py        # Event CRUD & Metric Calculations
│   └── attendance_service.py   # 5-Layer Anti-Proxy Verification Engine
├── routes/
│   ├── host_routes.py          # Organizer Dashboard & 25s Token Stream API
│   └── student_routes.py       # Mobile Check-in & Attendance Endpoints
├── utils/
│   ├── geo.py                  # Haversine Distance & Geofence Boundary Check
│   ├── token_generator.py      # itsdangerous 25s Signed Timed Token Generator
│   └── qr_generator.py         # Zero-Disk Base64 Dynamic QR Code Generator
├── templates/
│   ├── base.html               # Master SaaS Layout (Tailwind CSS, Inter Font)
│   ├── host/
│   │   ├── create_event.html   # Event Setup with 1-Click GPS Location Locking
│   │   ├── list_events.html    # Active Event Sessions Grid
│   │   └── dashboard.html      # Live 25s Dynamic QR Broadcast & Attendee Feed
│   └── student/
│       ├── checkin.html        # Mobile-First Check-in Form with Auto GPS Prompt
│       └── status.html         # Unified Status Result (Success / Expired / Out of Bounds)
├── static/
│   ├── css/custom.css          # Custom SaaS Styles, Cards & Progress Rings
│   └── js/
│       ├── host_dashboard.js   # 25s Countdown Bar & Live Attendee Poller
│       └── student_checkin.js  # High-Accuracy Geolocation API Handler
└── tests/
    ├── test_phase2.py          # Math & Cryptography Unit Tests
    ├── test_phase3.py          # Firestore Model & Service Tests
    ├── test_phase4.py          # Host Portal & Dynamic QR API Tests
    └── test_phase5.py          # Student Verification Pipeline Tests
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ installed
- Modern Web Browser (Chrome, Safari, Firefox, Edge)

### 2. Setup Virtual Environment & Dependencies

```bash
# Clone or navigate to the directory
cd GeoQR

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Default `.env` configuration:
```ini
SECRET_KEY=geoqr-super-secure-local-dev-secret-key-987654321
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_RUN_HOST=127.0.0.1
FLASK_RUN_PORT=5000

# Anti-Proxy 25-second token window
QR_TOKEN_MAX_AGE_SECONDS=25

# Firebase Service Account Path
FIREBASE_CREDENTIALS_PATH=firebase/serviceAccountKey.json
```

---

## 🔥 Firebase Firestore Setup

GeoQR automatically detects your Firebase configuration:
1. Open [Firebase Console](https://console.firebase.google.com/) and create a project.
2. Go to **Firestore Database** ➔ **Create Database**.
3. Go to **Project Settings (⚙️)** ➔ **Service Accounts** ➔ Click **"Generate new private key"**.
4. Save the downloaded JSON file as `firebase/serviceAccountKey.json`.

*(If no credentials file is found, GeoQR automatically switches to an in-memory Firestore emulator for local offline testing).*

---

## 🧪 Running Automated Tests

Run the full automated test suite (22 unit & integration tests):

```bash
python -m unittest discover tests
```

---

## 🖥️ Running the Application

Start the Flask development server:

```bash
python app.py
```

Then open your browser at:
- **Organizer / Host Portal**: `http://127.0.0.1:5000/host/create`
- **Events List**: `http://127.0.0.1:5000/host/events`
- **Health Check**: `http://127.0.0.1:5000/health`

---

## 📱 How to Test the Anti-Proxy System

### Step 1: Host Creates Event
1. Open `http://127.0.0.1:5000/host/create`.
2. Click **"Detect & Lock My Current Location"** (allows browser GPS).
3. Set your event radius (e.g. 50 meters) and click **"Create Event & Launch Live QR"**.

### Step 2: Live Dynamic QR Screen
1. The Host Dashboard opens with a large dynamic QR code.
2. Observe the **25-second countdown timer**. Every 25 seconds, the QR code rotates automatically.
3. Click the **"Copy"** button or scan the QR code with your mobile phone.

### Step 3: Student Checks In
1. The student check-in page opens on mobile and prompts for location permission.
2. Enter **Full Name** and **Student ID** (e.g. `CS2026-001`).
3. Tap **"Submit Attendance"**.
4. **Verified Attendance** is immediately recorded in Firebase, and the host's screen updates live with the new attendee!

---

## 🛡️ Anti-Proxy Edge Cases Handled

| Scenario | Result | System Response |
| :--- | :--- | :--- |
| **Classmate takes a photo of QR & forwards to friend at home** | ❌ Blocked | Friend at home is outside geofence radius ➔ `Too Far Away (Out of Bounds)`. |
| **Friend at home tries to scan after 25 seconds** | ❌ Blocked | Cryptographic timestamp exceeds 25s window ➔ `QR Code Expired`. |
| **Student tries to submit attendance twice** | ❌ Blocked | Duplicate check in Firestore ➔ `Already Checked In`. |
| **Student attempts to forge or modify token** | ❌ Blocked | HMAC cryptographic signature validation fails ➔ `Invalid/Tampered Token`. |
| **Legitimate student in classroom within 25s** | ✅ Accepted | All 5 security gates pass ➔ `Attendance Recorded`. |

---

## 📄 License
MIT License. Built for universities, student clubs, and academic institutions.
