# 🌆 CivicFix

**AI-Powered Urban Infrastructure Intelligence Platform**

---

## 🚨 Problem

Cities struggle to respond efficiently to everyday infrastructure failures — potholes, broken streetlights, flooding, unsafe sidewalks, and public space damage.  

Current reporting systems:  

- Are slow and manual  
- Lack transparency  
- Don’t prioritize severity effectively  
- Provide little accountability to residents  

**Consequences:**  

- Unsafe streets  
- Unequal service across neighborhoods  
- Loss of public trust  

---

## 💡 Solution

**CivicFix** is an AI-powered civic reporting and transparency platform that enables residents to report infrastructure issues while giving municipalities real-time intelligence and accountability metrics.  

**For Residents:**  

- Upload a photo of an issue  
- Add a short description  
- Automatically receive AI classification (pothole, streetlight, graffiti, trash) and severity scoring  
- See their report appear instantly on a public dashboard  

**For Municipal Administrators:**  

- View real-time issue heatmaps  
- Track response times  
- Prioritize high-risk hazards  
- Monitor service equity across neighborhoods  

---

## 💡 Inspiration

CivicFix was inspired by everyday problems in our communities — potholes left unfixed, broken streetlights making areas unsafe, and reports that disappear without updates.  

We wanted a platform that gives people a stronger voice while helping cities work efficiently. By combining AI with real-time data and public dashboards, CivicFix bridges the gap between residents and local government — turning complaints into actionable, visible progress.  

---

## 🎯 Alignment to Challenge Goals

CivicFix contributes to:  

- **Public safety** through early hazard detection  
- **Smarter, data-driven city planning**  
- **Equitable service** across neighborhoods  
- **Transparency** with public dashboards  
- **Community participation**  

---

## 🤖 AI Integration

- **Image Classification:** Detect issue types (pothole, streetlight, trash, graffiti)  
- **Severity Scoring:** Prioritize urgent cases  
- **Accountability:** All AI decisions are logged and stored for auditing  

---

## 🏗 Tech Stack

**Frontend:**  

- React  
- Interactive map visualization (Leaflet / Mapbox)  

**Backend:**  

- Python (FastAPI)  
- AI models: MobileNetV2, Google Gemini 2.5 Flash  
- REST API architecture  

**Database:**  

- PostgreSQL (structured civic data storage)  

**Infrastructure:**  

- Cloud-hosted deployment with scalable architecture  

---

## 🚧 Major Challenges

- Selecting AI models suitable for free tiers and lightweight deployment  
- Labeling and scoring issues accurately  
- Ensuring AI correctly identifies various problem types from photos  

---

## 🎉 Accomplishments

- Implemented AI model fallback for reliability  
- Live map that updates instantly with new reports  
- Public dashboard for transparency  
- Dashboard for municipal staff to prioritize work  
- Demonstrated a real solution for community-driven urban problem solving  

---

## 📚 Lessons Learned

- Integrating AI models into real-world features  
- Using a database to store and query geolocation data  
- Designing intuitive interfaces for all users  

---

## 📊 Impact

Even as a prototype, CivicFix demonstrates how AI can modernize local governance:  

- Reduce response times  
- Prevent minor hazards from escalating  
- Identify underserved neighborhoods  
- Improve civic engagement  

---

## 🚀 Next Steps

- AI narrative summaries (e.g., weekly issue reports and budget impact)  
- Data-driven budgeting strategies  
- Budget impact forecasting  
- Integration with official 311 systems  
- Equity analytics dashboard  

CivicFix is designed to scale from small townships to major metropolitan cities.  


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
