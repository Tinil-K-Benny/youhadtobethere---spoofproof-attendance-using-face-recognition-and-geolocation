import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import bcrypt

from backend.config import get_db
from backend.utils.helpers import serialize_doc

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    role: str
    username: str  # For admin it can be 'admin', for student it's roll_no
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    if req.role == "admin":
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        if req.password == admin_pass:
            return {"success": True, "message": "Admin logged in", "user": {"role": "admin", "name": "Admin"}}
        raise HTTPException(status_code=401, detail="Invalid admin password")
        
    elif req.role == "student":
        db = get_db()
        student = await db.students.find_one({"roll_no": req.username}, {"face_embedding": 0})
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
            
        hashed_password = student.get("password")
        if not hashed_password:
            raise HTTPException(status_code=401, detail="Student has no password set. Please contact admin.")
            
        if bcrypt.checkpw(req.password.encode('utf-8'), hashed_password.encode('utf-8')):
            return {
                "success": True, 
                "message": "Student logged in", 
                "user": {"role": "student", "roll_no": student["roll_no"], "name": student["name"]}
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid password")
            
    else:
        raise HTTPException(status_code=400, detail="Invalid role")
