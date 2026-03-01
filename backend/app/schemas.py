from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class ReportCreate(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    description: Optional[str] = None
    reporter_name: Optional[str] = "Anonymous"


class AIClassificationResult(BaseModel):
    category: str
    confidence: float
    severity: str
    severity_score: float
    estimated_repair_days: int
    estimated_cost: float
    description: str


class ReportResponse(BaseModel):
    id: uuid.UUID
    image_url: str
    category: str
    confidence: float
    severity: str
    severity_score: float
    description: Optional[str]
    latitude: float
    longitude: float
    address: Optional[str]
    neighborhood: Optional[str]
    status: str
    estimated_repair_days: Optional[int]
    estimated_cost: Optional[float]
    reporter_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    assigned_to: Optional[str]
    response_time_hours: Optional[float] = None

    class Config:
        from_attributes = True


class ReportUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    neighborhood: Optional[str] = None


class DashboardStats(BaseModel):
    total_reports: int
    open_cases: int
    in_progress: int
    resolved: int
    avg_response_time_hours: float
    category_breakdown: dict
    severity_breakdown: dict
    most_affected_neighborhood: Optional[str]
    total_budget_impact: float
    reports_today: int
    reports_this_week: int
    reports_this_month: int


class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    intensity: float
