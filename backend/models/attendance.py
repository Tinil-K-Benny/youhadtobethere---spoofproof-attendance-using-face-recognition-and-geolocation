from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AttendanceStatus(str, Enum):
    present = "present"
    late = "late"
    rejected = "rejected"


class RejectionReason(str, Enum):
    face_mismatch = "face_mismatch"
    out_of_zone = "out_of_zone"
    outside_schedule = "outside_schedule"


class LocationCaptured(BaseModel):
    lat: float
    lng: float


class AttendanceMarkRequest(BaseModel):
    class_id: str
    lat: float
    lng: float


class AttendanceLog(BaseModel):
    student_id: str
    class_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: AttendanceStatus
    face_match_score: float
    location_captured: LocationCaptured
    distance_from_zone_m: float
    rejection_reason: Optional[str] = None


class AttendanceResponse(BaseModel):
    success: bool
    status: str
    student_name: Optional[str] = None
    roll_no: Optional[str] = None
    face_match_score: Optional[float] = None
    distance_from_zone_m: Optional[float] = None
    rejection_reason: Optional[str] = None
    message: str
