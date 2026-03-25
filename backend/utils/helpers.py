from bson import ObjectId
from datetime import datetime
from typing import Any, Dict


def object_id_to_str(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB ObjectId fields to strings for JSON serialization."""
    if doc is None:
        return doc
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = object_id_to_str(value)
        elif isinstance(value, list):
            result[key] = [
                object_id_to_str(v) if isinstance(v, dict) else v for v in value
            ]
        else:
            result[key] = value
    return result


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare a MongoDB document for API response:
    - Rename '_id' to 'id' and stringify ObjectId
    - Stringify any nested ObjectId values
    """
    if doc is None:
        return doc
    doc = object_id_to_str(doc)
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    return doc


def now_utc() -> datetime:
    return datetime.utcnow()
