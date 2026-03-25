import os
import requests
from typing import Any, Dict, Optional

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def _safe_json(response) -> Dict[str, Any]:
    try:
        return response.json()
    except Exception:
        return {"detail": f"Server error ({response.status_code}): {response.text}"}


# ─── Auth ────────────────────────────────────────────────────────────────────

def login(role: str, username: str, password: str):
    r = requests.post(
        _url("/api/auth/login"),
        json={"role": role, "username": username, "password": password}
    )
    return _safe_json(r), r.status_code


# ─── Students ────────────────────────────────────────────────────────────────

def list_students() -> Dict[str, Any]:
    r = requests.get(_url("/api/students/"))
    r.raise_for_status()
    return _safe_json(r)


def get_student(roll_no: str) -> Dict[str, Any]:
    r = requests.get(_url(f"/api/students/{roll_no}"))
    r.raise_for_status()
    return _safe_json(r)


def register_student(name: str, roll_no: str, email: str, password: str, photo_bytes: bytes, filename: str) -> Dict[str, Any]:
    r = requests.post(
        _url("/api/students/register"),
        data={"name": name, "roll_no": roll_no, "email": email, "password": password},
        files={"photo": (filename, photo_bytes, "image/jpeg")},
    )
    return _safe_json(r), r.status_code


def delete_student(roll_no: str) -> Dict[str, Any]:
    r = requests.delete(_url(f"/api/students/{roll_no}"))
    return _safe_json(r), r.status_code


# ─── Classes ─────────────────────────────────────────────────────────────────

def list_classes() -> Dict[str, Any]:
    r = requests.get(_url("/api/classes/"))
    r.raise_for_status()
    return _safe_json(r)


def create_class(payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(_url("/api/classes/"), json=payload)
    return _safe_json(r), r.status_code


def update_class(class_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.put(_url(f"/api/classes/{class_id}"), json=payload)
    return _safe_json(r), r.status_code


def delete_class(class_id: str) -> Dict[str, Any]:
    r = requests.delete(_url(f"/api/classes/{class_id}"))
    return _safe_json(r), r.status_code


# ─── Attendance ───────────────────────────────────────────────────────────────

def mark_attendance(
    class_id: str,
    roll_no: str,
    lat: float,
    lng: float,
    image_bytes: bytes,
    filename: str = "snapshot.jpg",
) -> Dict[str, Any]:
    r = requests.post(
        _url("/api/attendance/mark"),
        data={"class_id": class_id, "roll_no": roll_no, "lat": lat, "lng": lng},
        files={"image": (filename, image_bytes, "image/jpeg")},
    )
    return _safe_json(r), r.status_code


def get_class_attendance(class_id: str) -> Dict[str, Any]:
    r = requests.get(_url(f"/api/attendance/class/{class_id}"))
    r.raise_for_status()
    return _safe_json(r)


def get_student_attendance(roll_no: str) -> Dict[str, Any]:
    r = requests.get(_url(f"/api/attendance/student/{roll_no}"))
    r.raise_for_status()
    return _safe_json(r)


def get_attendance_summary(class_id: str) -> Dict[str, Any]:
    r = requests.get(_url(f"/api/attendance/summary/{class_id}"))
    r.raise_for_status()
    return _safe_json(r)


def check_api_health() -> bool:
    try:
        r = requests.get(_url("/health"), timeout=3)
        return r.status_code == 200
    except Exception:
        return False
