from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime, time as dtime

from backend.config import get_db, FACE_MATCH_THRESHOLD
from backend.services import face_service, geo_service
from backend.utils.helpers import serialize_doc

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

DAYS_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


def _parse_time(t_str: str) -> dtime:
    h, m = map(int, t_str.split(":"))
    return dtime(h, m)


@router.post("/mark")
async def mark_attendance(
    class_id: str = Form(...),
    roll_no: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    image: UploadFile = File(...),
):
    db = get_db()

    # 1. Validate class_id and load class
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class_id.")
    class_doc = await db.classes.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found.")

    # 1.5 Load the logged-in student
    student = await db.students.find_one({"roll_no": roll_no})
    if not student:
        raise HTTPException(status_code=404, detail="Logged in student not found in database.")

    # 2. Encode face from uploaded image
    image_bytes = await image.read()
    embedding = face_service.encode_face(image_bytes)

    if embedding is None:
        return _rejected_response(
            face_match_score=1.0,
            lat=lat,
            lng=lng,
            distance=0.0,
            reason="face_mismatch",
            message="No face detected in the image.",
            student=student
        )

    # 3. Run face match strictly against the logged-in student
    matched_student, match_score = face_service.match_face(
        embedding, [student], threshold=FACE_MATCH_THRESHOLD
    )

    if matched_student is None:
        return _rejected_response(
            face_match_score=round(match_score, 4),
            lat=lat,
            lng=lng,
            distance=0.0,
            reason="face_mismatch",
            message=f"Face does not match your student profile (distance={match_score:.4f}).",
            student=student
        )

    # 4. Check schedule window
    utc_now = datetime.utcnow()
    local_now = datetime.now()
    # Use local weekday name
    current_day = DAYS_MAP[local_now.weekday()]
    schedule = class_doc["schedule"]

    if schedule["day"].strip().lower() != current_day.lower():
        return _rejected_response(
            face_match_score=round(match_score, 4),
            lat=lat,
            lng=lng,
            distance=0.0,
            reason="outside_schedule",
            message=f"No class scheduled today ({current_day}). Expected: {schedule['day']}.",
            student=matched_student,
        )

    current_time = local_now.time()
    start = _parse_time(schedule["start_time"])
    end = _parse_time(schedule["end_time"])

    if not (start <= current_time <= end):
        return _rejected_response(
            face_match_score=round(match_score, 4),
            lat=lat,
            lng=lng,
            distance=0.0,
            reason="outside_schedule",
            message=f"Outside class window ({schedule['start_time']} – {schedule['end_time']}).",
            student=matched_student,
        )

    # Determine status: present if within first 10 min, otherwise late
    start_dt = datetime.combine(local_now.date(), start)
    late_threshold = (start_dt.timestamp() + 10 * 60)  # 10 minutes grace
    status = "present" if local_now.timestamp() <= late_threshold else "late"

    # 5. Check geolocation
    zone = class_doc["location_zone"]
    within_zone, distance_m = geo_service.is_within_zone(
        lat, lng, zone["lat"], zone["lng"], zone["radius_meters"]
    )

    if not within_zone:
        return _rejected_response(
            face_match_score=round(match_score, 4),
            lat=lat,
            lng=lng,
            distance=distance_m,
            reason="out_of_zone",
            message=f"You are {distance_m:.1f}m from the classroom (allowed: {zone['radius_meters']}m).",
            student=matched_student,
        )

    # 5.5 Prevent Duplicate Attendance
    from datetime import timedelta
    twelve_hours_ago = utc_now - timedelta(hours=12)
    existing_log = await db.attendance_logs.find_one({
        "student_id": matched_student["_id"],
        "class_id": ObjectId(class_id),
        "status": {"$in": ["present", "late"]},
        "timestamp": {"$gte": twelve_hours_ago}
    })

    if existing_log:
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "status": "already_marked",
                "student_name": matched_student["name"],
                "roll_no": matched_student["roll_no"],
                "face_match_score": round(match_score, 4),
                "distance_from_zone_m": distance_m,
                "rejection_reason": "duplicate",
                "message": f"Attendance is already marked for {matched_student['name']} today."
            }
        )

    # 6. All checks passed — insert attendance log
    log = {
        "student_id": matched_student["_id"],
        "class_id": ObjectId(class_id),
        "timestamp": utc_now,
        "status": status,
        "face_match_score": round(match_score, 4),
        "location_captured": {"lat": lat, "lng": lng},
        "distance_from_zone_m": distance_m,
        "rejection_reason": None,
    }
    await db.attendance_logs.insert_one(log)

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "status": status,
            "student_name": matched_student["name"],
            "roll_no": matched_student["roll_no"],
            "face_match_score": round(match_score, 4),
            "distance_from_zone_m": distance_m,
            "rejection_reason": None,
            "message": f"Attendance marked as '{status}' for {matched_student['name']}.",
        },
    )


def _rejected_response(
    face_match_score: float,
    lat: float,
    lng: float,
    distance: float,
    reason: str,
    message: str,
    student=None,
):
    log_data = {
        "student_id": student["_id"] if student else None,
        "class_id": None,
        "timestamp": datetime.utcnow(),
        "status": "rejected",
        "face_match_score": face_match_score,
        "location_captured": {"lat": lat, "lng": lng},
        "distance_from_zone_m": distance,
        "rejection_reason": reason,
    }
    # We don't await here since this is a sync helper — caller must handle logging separately if needed
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "status": "rejected",
            "student_name": student["name"] if student else None,
            "roll_no": student["roll_no"] if student else None,
            "face_match_score": face_match_score,
            "distance_from_zone_m": distance,
            "rejection_reason": reason,
            "message": message,
        },
    )


@router.get("/class/{class_id}")
async def get_class_attendance(class_id: str):
    db = get_db()
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class_id.")

    logs = []
    async for log in db.attendance_logs.find({"class_id": ObjectId(class_id)}).sort("timestamp", -1):
        log_data = serialize_doc(log)
        # Enrich with student name
        if log.get("student_id"):
            student = await db.students.find_one(
                {"_id": log["student_id"]}, {"name": 1, "roll_no": 1}
            )
            if student:
                log_data["student_name"] = student["name"]
                log_data["roll_no"] = student["roll_no"]
        logs.append(log_data)

    return {"logs": logs, "total": len(logs)}


@router.get("/student/{roll_no}")
async def get_student_attendance(roll_no: str):
    db = get_db()
    student = await db.students.find_one({"roll_no": roll_no}, {"_id": 1, "name": 1})
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{roll_no}' not found.")

    logs = []
    async for log in db.attendance_logs.find(
        {"student_id": student["_id"]}
    ).sort("timestamp", -1):
        log_data = serialize_doc(log)
        log_data["student_name"] = student["name"]
        log_data["roll_no"] = roll_no
        logs.append(log_data)

    return {"student": roll_no, "logs": logs, "total": len(logs)}


@router.get("/summary/{class_id}")
async def get_attendance_summary(class_id: str):
    db = get_db()
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class_id.")

    class_doc = await db.classes.find_one({"_id": ObjectId(class_id)})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found.")

    # Build per-student summary
    pipeline = [
        {"$match": {"class_id": ObjectId(class_id)}},
        {
            "$group": {
                "_id": "$student_id",
                "total": {"$sum": 1},
                "present": {
                    "$sum": {"$cond": [{"$in": ["$status", ["present", "late"]]}, 1, 0]}
                },
                "rejected": {
                    "$sum": {"$cond": [{"$eq": ["$status", "rejected"]}, 1, 0]}
                },
            }
        },
    ]

    summary = []
    async for row in db.attendance_logs.aggregate(pipeline):
        student = await db.students.find_one(
            {"_id": row["_id"]}, {"name": 1, "roll_no": 1}
        )
        pct = round((row["present"] / row["total"]) * 100, 1) if row["total"] > 0 else 0
        summary.append(
            {
                "student_id": str(row["_id"]),
                "student_name": student["name"] if student else "Unknown",
                "roll_no": student["roll_no"] if student else "N/A",
                "total_attempts": row["total"],
                "present_count": row["present"],
                "rejected_count": row["rejected"],
                "attendance_percentage": pct,
            }
        )

    return {
        "class_id": class_id,
        "subject": class_doc["subject"],
        "summary": sorted(summary, key=lambda x: x["roll_no"]),
    }
