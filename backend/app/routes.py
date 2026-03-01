"""
API routes for CivicFix reports.
"""

import os
import uuid
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from app.database import get_db
from app.models import Report, IssueCategory, Severity, ReportStatus
from app.schemas import (
    ReportResponse, ReportUpdate, DashboardStats, HeatmapPoint, AIClassificationResult,
)
from app.ai_classifier import classify_image
from app.config import settings

router = APIRouter(prefix="/api", tags=["reports"])


# ── Upload & Classify ──────────────────────────────────────
@router.post("/reports", response_model=ReportResponse)
async def create_report(
    file: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: Optional[str] = Form(None),
    neighborhood: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    reporter_name: Optional[str] = Form("Anonymous"),
    db: Session = Depends(get_db),
):
    """Upload photo, run AI classification, create report."""
    # Read image
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(400, "Empty file uploaded")

    # Save file
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_ext = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{file_ext}"
    filepath = os.path.join(settings.upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    # AI Classification
    ai_result = classify_image(contents, file.filename or "")

    # Create report
    report = Report(
        id=uuid.uuid4(),
        image_url=f"/uploads/{filename}",
        category=IssueCategory(ai_result["category"]),
        confidence=ai_result["confidence"],
        severity=Severity(ai_result["severity"]),
        severity_score=ai_result["severity_score"],
        description=ai_result["description"],
        latitude=latitude,
        longitude=longitude,
        address=address,
        neighborhood=neighborhood or "Unknown",
        status=ReportStatus.OPEN,
        estimated_repair_days=ai_result["estimated_repair_days"],
        estimated_cost=ai_result["estimated_cost"],
        reporter_name=reporter_name,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return _report_to_response(report)


# ── List Reports ───────────────────────────────────────────
@router.get("/reports", response_model=list[ReportResponse])
def list_reports(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    neighborhood: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """List all reports with optional filters."""
    q = db.query(Report)
    if status:
        q = q.filter(Report.status == status)
    if category:
        q = q.filter(Report.category == category)
    if severity:
        q = q.filter(Report.severity == severity)
    if neighborhood:
        q = q.filter(Report.neighborhood == neighborhood)

    reports = q.order_by(desc(Report.created_at)).offset(offset).limit(limit).all()
    return [_report_to_response(r) for r in reports]


# ── Single Report ──────────────────────────────────────────
@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    return _report_to_response(report)


# ── Update Report (Admin) ─────────────────────────────────
@router.patch("/reports/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: uuid.UUID,
    update: ReportUpdate,
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")

    if update.status:
        report.status = ReportStatus(update.status)
        if update.status == "resolved":
            report.resolved_at = datetime.datetime.utcnow()
    if update.assigned_to is not None:
        report.assigned_to = update.assigned_to
    if update.neighborhood is not None:
        report.neighborhood = update.neighborhood

    report.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(report)
    return _report_to_response(report)


# ── Dashboard Stats ────────────────────────────────────────
@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - datetime.timedelta(days=7)
    month_start = today_start - datetime.timedelta(days=30)

    total = db.query(func.count(Report.id)).scalar() or 0
    open_count = db.query(func.count(Report.id)).filter(Report.status == ReportStatus.OPEN).scalar() or 0
    in_progress = db.query(func.count(Report.id)).filter(Report.status == ReportStatus.IN_PROGRESS).scalar() or 0
    resolved = db.query(func.count(Report.id)).filter(
        Report.status.in_([ReportStatus.RESOLVED, ReportStatus.CLOSED])
    ).scalar() or 0

    # Average response time (resolved reports only)
    resolved_reports = db.query(Report).filter(
        Report.resolved_at.isnot(None),
        Report.created_at.isnot(None),
    ).all()
    if resolved_reports:
        total_hours = sum(
            (r.resolved_at - r.created_at).total_seconds() / 3600
            for r in resolved_reports
        )
        avg_response = round(total_hours / len(resolved_reports), 1)
    else:
        avg_response = 0.0

    # Category breakdown
    cat_rows = db.query(
        Report.category, func.count(Report.id)
    ).group_by(Report.category).all()
    category_breakdown = {str(c.value) if hasattr(c, 'value') else str(c): cnt for c, cnt in cat_rows}

    # Severity breakdown
    sev_rows = db.query(
        Report.severity, func.count(Report.id)
    ).group_by(Report.severity).all()
    severity_breakdown = {str(s.value) if hasattr(s, 'value') else str(s): cnt for s, cnt in sev_rows}

    # Most affected neighborhood
    nbr_row = db.query(
        Report.neighborhood, func.count(Report.id).label("cnt")
    ).group_by(Report.neighborhood).order_by(desc("cnt")).first()
    most_affected = nbr_row[0] if nbr_row else None

    # Budget impact
    total_cost = db.query(func.sum(Report.estimated_cost)).scalar() or 0.0

    # Time-based counts
    today_count = db.query(func.count(Report.id)).filter(Report.created_at >= today_start).scalar() or 0
    week_count = db.query(func.count(Report.id)).filter(Report.created_at >= week_start).scalar() or 0
    month_count = db.query(func.count(Report.id)).filter(Report.created_at >= month_start).scalar() or 0

    return DashboardStats(
        total_reports=total,
        open_cases=open_count,
        in_progress=in_progress,
        resolved=resolved,
        avg_response_time_hours=avg_response,
        category_breakdown=category_breakdown,
        severity_breakdown=severity_breakdown,
        most_affected_neighborhood=most_affected,
        total_budget_impact=round(total_cost, 2),
        reports_today=today_count,
        reports_this_week=week_count,
        reports_this_month=month_count,
    )


# ── Heatmap Data ───────────────────────────────────────────
@router.get("/dashboard/heatmap", response_model=list[HeatmapPoint])
def heatmap_data(db: Session = Depends(get_db)):
    reports = db.query(
        Report.latitude, Report.longitude, Report.severity_score
    ).filter(Report.status.in_([ReportStatus.OPEN, ReportStatus.IN_PROGRESS])).all()

    return [
        HeatmapPoint(latitude=r.latitude, longitude=r.longitude, intensity=r.severity_score)
        for r in reports
    ]


# ── Neighborhoods List ─────────────────────────────────────
@router.get("/neighborhoods")
def list_neighborhoods(db: Session = Depends(get_db)):
    rows = db.query(
        Report.neighborhood, func.count(Report.id).label("count")
    ).group_by(Report.neighborhood).order_by(desc("count")).all()
    return [{"name": n, "count": c} for n, c in rows if n]


# ── AI-only endpoint (classify without saving) ────────────
@router.post("/classify", response_model=AIClassificationResult)
async def classify_only(file: UploadFile = File(...)):
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(400, "Empty file")
    result = classify_image(contents, file.filename or "")
    return AIClassificationResult(**result)


# ── Helper ─────────────────────────────────────────────────
def _report_to_response(report: Report) -> ReportResponse:
    return ReportResponse(
        id=report.id,
        image_url=report.image_url,
        category=report.category.value if hasattr(report.category, 'value') else str(report.category),
        confidence=report.confidence,
        severity=report.severity.value if hasattr(report.severity, 'value') else str(report.severity),
        severity_score=report.severity_score,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        address=report.address,
        neighborhood=report.neighborhood,
        status=report.status.value if hasattr(report.status, 'value') else str(report.status),
        estimated_repair_days=report.estimated_repair_days,
        estimated_cost=report.estimated_cost,
        reporter_name=report.reporter_name,
        created_at=report.created_at,
        updated_at=report.updated_at,
        resolved_at=report.resolved_at,
        assigned_to=report.assigned_to,
        response_time_hours=report.response_time_hours,
    )
