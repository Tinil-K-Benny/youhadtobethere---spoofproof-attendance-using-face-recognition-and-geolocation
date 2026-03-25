import numpy as np
import cv2
import face_recognition
from typing import List, Optional, Tuple, Dict, Any


def encode_face(image_bytes: bytes) -> Optional[List[float]]:
    """
    Takes raw image bytes, detects the first face, and returns a 128-float
    face embedding. Returns None if no face is detected.
    """
    np_arr = np.frombuffer(image_bytes, np.uint8)
    bgr_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if bgr_image is None:
        return None

    # face_recognition expects RGB
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    encodings = face_recognition.face_encodings(rgb_image)
    if not encodings:
        return None

    # Return first detected face embedding as plain Python list
    return encodings[0].tolist()


def match_face(
    embedding: List[float],
    all_students: List[Dict[str, Any]],
    threshold: float = 0.6,
) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Compare a face embedding against all stored student embeddings.

    Uses face_recognition.face_distance() — lower distance = more similar.
    Accepts a match if the minimum distance is below `threshold`.

    Returns:
        (best_match_student | None, match_distance_score)
        where score is the raw face distance (lower = better match).
    """
    if not all_students:
        return None, 1.0

    query_encoding = np.array(embedding)

    known_encodings = []
    valid_students = []

    for student in all_students:
        emb = student.get("face_embedding")
        if emb and len(emb) == 128:
            known_encodings.append(np.array(emb))
            valid_students.append(student)

    if not known_encodings:
        return None, 1.0

    distances = face_recognition.face_distance(known_encodings, query_encoding)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])

    if best_distance < threshold:
        return valid_students[best_idx], best_distance

    return None, best_distance
