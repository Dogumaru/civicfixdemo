# CivicFix – AI-Powered City Issue Reporter

A full-stack web application where citizens upload photos of city damage and AI instantly classifies the issue, assigns severity, plots it on a live map, and provides a government operations dashboard.

## Tech Stack

| Layer    | Technology         |
|----------|--------------------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend  | Python FastAPI     |
| Database | PostgreSQL 16      |
| Maps     | Leaflet / React-Leaflet |
| Charts   | Recharts           |
| AI       | Simulated CNN classifier (demo) |

## Features

### 1. Live Upload + Instant AI Classification
- Upload a photo of city damage
- AI instantly classifies: **pothole, streetlight, trash, graffiti**
- Returns confidence score, severity rating, repair urgency, and cost estimate

### 2. Auto-Plotted Map
- Every report pins on a **live interactive map**
- Color-coded markers by severity (green → red)
- Toggle **heat zone overlay** showing problem density
- Filter by category

### 3. Public Dashboard
- Real-time KPI cards (open cases, resolved, avg response time)
- Category breakdown bar chart
- Severity distribution donut chart
- Reports over time area chart
- Most affected neighborhood highlight

### 4. Government Admin Dashboard
- **Township Admin Mode** with full case management
- Open/close/assign cases with inline controls
- Most affected neighborhoods horizontal bar chart
- Budget impact by severity
- Filter by status, category, severity
- Avg response time tracking

---

## Quick Start

### Option A: Docker (Recommended)

```bash
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option B: Manual Setup

#### 1. PostgreSQL
```bash
# Make sure PostgreSQL is running, then create the database:
psql -U postgres
CREATE DATABASE civicfix;
CREATE USER civicfix WITH PASSWORD 'civicfix';
GRANT ALL PRIVILEGES ON DATABASE civicfix TO civicfix;
\q
```

#### 2. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Method | Endpoint               | Description                      |
|--------|------------------------|----------------------------------|
| POST   | `/api/reports`         | Upload photo + create report     |
| GET    | `/api/reports`         | List all reports (with filters)  |
| GET    | `/api/reports/{id}`    | Get single report                |
| PATCH  | `/api/reports/{id}`    | Update status/assignment         |
| POST   | `/api/classify`        | Classify image only (no save)    |
| GET    | `/api/dashboard/stats` | Dashboard statistics             |
| GET    | `/api/dashboard/heatmap` | Heatmap coordinates            |
| GET    | `/api/neighborhoods`   | List neighborhoods by count      |

## Demo Script

1. **Open** http://localhost:5173
2. **Upload** any photo (pothole, trash, etc.)
3. **Watch** AI instantly return classification:
   > "Pothole detected – 87% confidence"  
   > Severity: **HIGH**  
   > Estimated repair urgency: **3 days**
4. **Navigate to Map** → see the new pin drop with heat zones
5. **Open Dashboard** → see live counts update
6. **Switch to Admin** → Township Admin Mode with case management

## Project Structure

```
civicfixdemo/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry
│   │   ├── config.py         # Environment settings
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── models.py         # Database models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── routes.py         # API endpoints
│   │   ├── ai_classifier.py  # AI classification engine
│   │   └── seed.py           # Demo data generator
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # React entry
│   │   ├── App.jsx           # Router + layout
│   │   ├── api.js            # API client
│   │   ├── index.css         # Tailwind + custom styles
│   │   └── pages/
│   │       ├── ReportPage.jsx    # Upload + AI classification
│   │       ├── MapPage.jsx       # Interactive map
│   │       ├── DashboardPage.jsx # Public analytics
│   │       └── AdminPage.jsx     # Government admin
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```
