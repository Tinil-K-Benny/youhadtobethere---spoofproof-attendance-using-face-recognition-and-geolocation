from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Schedule(BaseModel):
    day: str  # Monday, Tuesday, ...
    start_time: str  # HH:MM
    end_time: str  # HH:MM


class LocationZone(BaseModel):
    lat: float
    lng: float
    radius_meters: int


class ClassCreate(BaseModel):
    subject: str
    subject_code: str
    teacher: str
    schedule: Schedule
    location_zone: LocationZone


class ClassUpdate(BaseModel):
    subject: Optional[str] = None
    subject_code: Optional[str] = None
    teacher: Optional[str] = None
    schedule: Optional[Schedule] = None
    location_zone: Optional[LocationZone] = None


class ClassResponse(BaseModel):
    id: str
    subject: str
    subject_code: str
    teacher: str
    schedule: Schedule
    location_zone: LocationZone
    created_at: datetime
