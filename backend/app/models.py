import uuid
import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class IssueCategory(str, enum.Enum):
    POTHOLE = "pothole"
    STREETLIGHT = "streetlight"
    TRASH = "trash"
    GRAFFITI = "graffiti"
    OTHER = "other"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_url = Column(String(500), nullable=False)
    category = Column(SAEnum(IssueCategory), nullable=False)
    confidence = Column(Float, nullable=False)
    severity = Column(SAEnum(Severity), nullable=False)
    severity_score = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500), nullable=True)
    neighborhood = Column(String(200), nullable=True)
    status = Column(SAEnum(ReportStatus), default=ReportStatus.OPEN)
    estimated_repair_days = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    reporter_name = Column(String(200), nullable=True, default="Anonymous")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    assigned_to = Column(String(200), nullable=True)

    @property
    def response_time_hours(self):
        if self.resolved_at and self.created_at:
            delta = self.resolved_at - self.created_at
            return round(delta.total_seconds() / 3600, 1)
        return None
