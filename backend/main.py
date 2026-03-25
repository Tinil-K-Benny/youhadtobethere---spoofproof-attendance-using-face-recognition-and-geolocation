from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.config import connect_to_mongo, close_mongo_connection, UPLOAD_DIR
from backend.routes import students, classes, attendance, auth

app = FastAPI(
    title="FaceCheck API",
    description="Face Recognition + Geolocation Attendance System",
    version="1.0.0",
)

# CORS — allow Streamlit frontend (and any local dev origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded photos
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Register routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(classes.router)
app.include_router(attendance.router)


@app.on_event("startup")
async def startup():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "FaceCheck API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
