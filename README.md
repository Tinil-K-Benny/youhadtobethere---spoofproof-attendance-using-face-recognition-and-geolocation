# FaceCheck

> **Face Recognition + Geolocation Attendance System**

FaceCheck is a full-stack attendance management system that uses face recognition and GPS verification to automatically mark students as present, late, or rejected — with three-factor verification:

1. **Face match** — compares submitted snapshot against registered face embeddings
2. **Geo-zone check** — verifies the student is physically within the classroom GPS zone
3. **Schedule window** — confirms submission is within the configured class time

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + Uvicorn |
| Database | MongoDB (async via Motor) |
| Face Recognition | `face_recognition` (dlib) |
| Image Processing | OpenCV |
| Frontend | Streamlit |
| Geolocation | Haversine formula |

---

## Project Structure

```
facecheck/
├── backend/
│   ├── main.py              # FastAPI app + CORS + routers
│   ├── config.py            # MongoDB connection + env vars
│   ├── models/              # Pydantic schemas
│   ├── routes/              # API endpoints
│   ├── services/            # face_service, geo_service
│   └── utils/               # helpers (serialization)
├── frontend/
│   ├── app.py               # Streamlit home page
│   ├── pages/               # Multipage Streamlit app
│   └── utils/api_client.py  # HTTP client for FastAPI
├── uploads/                 # Stored face photos
├── .env
├── requirements.txt
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.9+
- MongoDB running locally (default: `localhost:27017`)
- CMake + C++ build tools (required for `dlib`/`face_recognition`)

### 1. Install dependencies

```bash
cd facecheck
pip install -r requirements.txt
```

> **Windows note:** `face-recognition` requires `dlib`. Install CMake first:
> ```
> pip install cmake
> pip install dlib
> pip install face-recognition
> ```

### 2. Configure environment

Copy or edit `.env`:

```env
MONGODB_URI=mongodb://localhost:27017
DB_NAME=facecheck
FACE_MATCH_THRESHOLD=0.6
API_BASE_URL=http://localhost:8000
UPLOAD_DIR=uploads
```

---

## Running the System

### Start MongoDB

Make sure MongoDB is running:

```bash
mongod
# or as a service: net start MongoDB
```

### Start the Backend (FastAPI)

Run from the **`facecheck/` root directory**:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Start the Frontend (Streamlit)

In a **second terminal**, from the `facecheck/` root:

```bash
streamlit run frontend/app.py
```

Frontend available at: [http://localhost:8501](http://localhost:8501)

---

## How to Use

### Register a Student

1. Open the app → **Register Student** page
2. Fill in name, roll number, and email
3. Upload a clear frontal face photo
4. Click **Register Student**
5. The backend extracts the 128-dim face embedding and stores it in MongoDB

### Mark Attendance

1. Go to **Mark Attendance** page
2. Select the class from the dropdown
3. Click **Take a snapshot** to capture your face
4. Allow browser GPS or enter coordinates manually
5. Click **Submit Attendance**
6. Result will show: ✅ Present / ⏰ Late / ❌ Rejected (with reason)

### View Dashboard

1. Go to **Dashboard** page
2. Select a class
3. View attendance %, bar charts, pie charts, and recent logs

### Manage Classes

1. Go to **Manage Classes** page
2. Fill in subject, code, teacher, schedule, and GPS zone
3. Click **Create Class**
4. Edit the GPS zone or delete classes from the list

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/students/register` | Register student with face photo |
| GET | `/api/students/` | List all students |
| GET | `/api/students/{roll_no}` | Get student by roll number |
| DELETE | `/api/students/{roll_no}` | Delete student |
| POST | `/api/attendance/mark` | Mark attendance |
| GET | `/api/attendance/class/{class_id}` | Logs for a class |
| GET | `/api/attendance/student/{roll_no}` | Student attendance history |
| GET | `/api/attendance/summary/{class_id}` | Summary % per student |
| POST | `/api/classes/` | Create class session |
| GET | `/api/classes/` | List classes |
| PUT | `/api/classes/{class_id}` | Update class |
| DELETE | `/api/classes/{class_id}` | Delete class |

---

## MongoDB Setup

Collections are created automatically on first run with appropriate indexes.

Manual MongoDB connection test:

```bash
mongosh mongodb://localhost:27017/facecheck
```

---

## Face Match Threshold

The default threshold is `0.6` (face distance, not similarity). **Lower = stricter**:

| Value | Effect |
|-------|--------|
| `0.4` | Very strict — few false positives |
| `0.6` | Balanced (default) |
| `0.7` | Lenient — more false positives possible |

Adjust in `.env`: `FACE_MATCH_THRESHOLD=0.6`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `dlib` install error | Install CMake first: `pip install cmake` |
| No face detected | Use a well-lit frontal photo |
| GPS not working | Enter coordinates manually or use HTTPS |
| API not reachable | Confirm `uvicorn` is running and check firewall |
| `duplicate key error` | Roll number already registered |
