from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime

from backend.config import get_db
from backend.models.class_session import ClassCreate, ClassUpdate
from backend.utils.helpers import serialize_doc

router = APIRouter(prefix="/api/classes", tags=["Classes"])


def _validate_object_id(class_id: str):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail=f"Invalid class_id: '{class_id}'")
    return ObjectId(class_id)


@router.post("/")
async def create_class(data: ClassCreate):
    db = get_db()
    doc = {
        **data.model_dump(),
        "created_at": datetime.utcnow(),
    }
    result = await db.classes.insert_one(doc)
    doc["_id"] = result.inserted_id
    return JSONResponse(
        status_code=201,
        content={"success": True, "class": serialize_doc(doc)},
    )


@router.get("/")
async def list_classes():
    db = get_db()
    classes = []
    async for doc in db.classes.find({}):
        classes.append(serialize_doc(doc))
    return {"classes": classes, "total": len(classes)}


@router.put("/{class_id}")
async def update_class(class_id: str, data: ClassUpdate):
    db = get_db()
    oid = _validate_object_id(class_id)

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    result = await db.classes.update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Class '{class_id}' not found.")

    updated = await db.classes.find_one({"_id": oid})
    return {"success": True, "class": serialize_doc(updated)}


@router.delete("/{class_id}")
async def delete_class(class_id: str):
    db = get_db()
    oid = _validate_object_id(class_id)
    result = await db.classes.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Class '{class_id}' not found.")
    return {"success": True, "message": f"Class '{class_id}' deleted."}
