from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class StudentRegister(BaseModel):
    name: str
    roll_no: str
    email: str


class StudentResponse(BaseModel):
    id: str
    name: str
    roll_no: str
    email: str
    registered_at: datetime
    photo_path: Optional[str] = None

    class Config:
        from_attributes = True


class StudentInDB(BaseModel):
    name: str
    roll_no: str
    email: str
    face_embedding: List[float]
    photo_path: Optional[str] = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)
