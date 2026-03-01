"""
Seed data generator for CivicFix demo.
Generates realistic sample reports across a city grid.
"""

import uuid
import random
import datetime
from sqlalchemy.orm import Session
from app.models import Report, IssueCategory, Severity, ReportStatus

# ── Philadelphia-area coordinates (for demo) ──
CENTER_LAT = 39.9526
CENTER_LNG = -75.1652

NEIGHBORHOODS = [
    "Center City", "University City", "Fishtown", "Kensington",
    "Northern Liberties", "South Philly", "Germantown", "Manayunk",
    "Roxborough", "Chestnut Hill", "Old City", "Rittenhouse Square",
    "Fairmount", "Spring Garden", "Port Richmond"
]

STREETS = [
    "Broad St", "Market St", "Walnut St", "Chestnut St", "Spring Garden St",
    "Girard Ave", "Passyunk Ave", "Front St", "2nd St", "5th St",
    "Oregon Ave", "Washington Ave", "Vine St", "Race St", "Arch St"
]

ASSIGNEES = [
    "John Martinez", "Sarah Chen", "Mike O'Brien", "Lisa Washington",
    "David Kim", "Rachel Torres", None, None  # Some unassigned
]


def _random_coord():
    lat = CENTER_LAT + random.uniform(-0.04, 0.04)
    lng = CENTER_LNG + random.uniform(-0.06, 0.06)
    return round(lat, 6), round(lng, 6)


def _random_past_date(days_back=90):
    return datetime.datetime.utcnow() - datetime.timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )


def seed_database(db: Session, count: int = 75):
    """Generate sample reports for demo."""
    existing = db.query(Report).count()
    if existing >= 10:
        print(f"Database already has {existing} reports, skipping seed.")
        return

    categories = list(IssueCategory)
    severities = list(Severity)
    statuses = list(ReportStatus)

    # Weight distributions for realistic demo
    category_weights = [0.35, 0.20, 0.25, 0.15, 0.05]  # pothole heavy
    severity_weights = [0.15, 0.30, 0.35, 0.20]
    status_weights = [0.35, 0.25, 0.30, 0.10]

    reports = []
    for i in range(count):
        cat = random.choices(categories, weights=category_weights, k=1)[0]
        sev = random.choices(severities, weights=severity_weights, k=1)[0]
        stat = random.choices(statuses, weights=status_weights, k=1)[0]
        lat, lng = _random_coord()
        created = _random_past_date()
        neighborhood = random.choice(NEIGHBORHOODS)
        street = random.choice(STREETS)

        resolved_at = None
        if stat in (ReportStatus.RESOLVED, ReportStatus.CLOSED):
            resolved_at = created + datetime.timedelta(
                hours=random.randint(2, 168)
            )

        cost_map = {
            Severity.LOW: (100, 500),
            Severity.MEDIUM: (500, 1500),
            Severity.HIGH: (1500, 4000),
            Severity.CRITICAL: (4000, 10000),
        }
        repair_map = {
            Severity.LOW: 14,
            Severity.MEDIUM: 7,
            Severity.HIGH: 3,
            Severity.CRITICAL: 1,
        }

        cost_range = cost_map[sev]
        report = Report(
            id=uuid.uuid4(),
            image_url=f"/uploads/sample_{cat.value}_{i}.jpg",
            category=cat,
            confidence=round(random.uniform(0.72, 0.97), 2),
            severity=sev,
            severity_score=round(random.uniform(0.2, 1.0), 2),
            description=f"{cat.value.title()} issue at {street}, {neighborhood}",
            latitude=lat,
            longitude=lng,
            address=f"{random.randint(100,9999)} {street}",
            neighborhood=neighborhood,
            status=stat,
            estimated_repair_days=repair_map[sev],
            estimated_cost=round(random.uniform(*cost_range), 2),
            reporter_name=random.choice(["Anonymous", "John D.", "Maria S.", "Alex T.", "Priya K.", "James W."]),
            created_at=created,
            updated_at=created + datetime.timedelta(hours=random.randint(0, 48)),
            resolved_at=resolved_at,
            assigned_to=random.choice(ASSIGNEES),
        )
        reports.append(report)

    db.add_all(reports)
    db.commit()
    print(f"✓ Seeded {count} demo reports")
