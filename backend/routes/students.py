import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime

from backend.config import get_db, UPLOAD_DIR
from backend.services import face_service
from backend.utils.helpers import serialize_doc

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.post("/register")
async def register_student(
    name: str = Form(...),
    roll_no: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    photo: UploadFile = File(...),
):
    db = get_db()

    # Check for duplicate roll_no
    existing = await db.students.find_one({"roll_no": roll_no})
    if existing:
        raise HTTPException(status_code=400, detail=f"Student with roll_no '{roll_no}' already exists.")

    image_bytes = await photo.read()

    # Encode face
    embedding = face_service.encode_face(image_bytes)
    if embedding is None:
        raise HTTPException(
            status_code=422,
            detail="No face detected in the uploaded photo. Please use a clear frontal face image.",
        )

    # Save photo to disk
    photo_filename = f"{roll_no}_{photo.filename}"
    photo_path = os.path.join(UPLOAD_DIR, photo_filename)
    with open(photo_path, "wb") as f:
        f.write(image_bytes)

    # Hash the password
    import bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    doc = {
        "name": name,
        "roll_no": roll_no,
        "email": email,
        "password": hashed_password,
        "face_embedding": embedding,
        "photo_path": photo_path,
        "registered_at": datetime.utcnow(),
    }

    result = await db.students.insert_one(doc)
    doc["_id"] = result.inserted_id

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "message": f"Student '{name}' registered successfully.",
            "student": serialize_doc(doc),
        },
    )


@router.get("/")
async def list_students():
    db = get_db()
    cursor = db.students.find({}, {"face_embedding": 0, "password": 0})  # exclude sensitive fields
    students = []
    async for doc in cursor:
        students.append(serialize_doc(doc))
    return {"students": students, "total": len(students)}


@router.get("/{roll_no}")
async def get_student(roll_no: str):
    db = get_db()
    doc = await db.students.find_one({"roll_no": roll_no}, {"face_embedding": 0, "password": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Student '{roll_no}' not found.")
    return serialize_doc(doc)


@router.delete("/{roll_no}")
async def delete_student(roll_no: str):
    db = get_db()
    doc = await db.students.find_one({"roll_no": roll_no})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Student '{roll_no}' not found.")

    # Remove photo from disk if present
    if doc.get("photo_path") and os.path.exists(doc["photo_path"]):
        os.remove(doc["photo_path"])

    await db.students.delete_one({"roll_no": roll_no})
    return {"success": True, "message": f"Student '{roll_no}' deleted."}
